import argparse
import random
import sys
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from src import CLASS_NAMES
from src.model import build_skin_type_model, enable_upper_layer_fine_tuning
from src.utils import load_config


def build_dataset(
    rows,
    data_root,
    input_size,
    batch_size,
    training,
    seed,
    augmentation_config=None,
):
    import tensorflow as tf

    paths = [str(data_root / row["relative_path"]) for row in rows]
    labels = [CLASS_NAMES.index(row["skin_type_label"]) for row in rows]
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        dataset = dataset.shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)

    augmentation_config = augmentation_config or {}
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal", seed=seed),
            tf.keras.layers.RandomRotation(
                float(augmentation_config.get("rotation_degrees", 8)) / 360.0,
                fill_mode="reflect",
                seed=seed,
            ),
            tf.keras.layers.RandomTranslation(
                float(augmentation_config.get("translation_fraction", 0.05)),
                float(augmentation_config.get("translation_fraction", 0.05)),
                fill_mode="reflect",
                seed=seed,
            ),
            tf.keras.layers.RandomZoom(
                float(augmentation_config.get("zoom_fraction", 0.10)),
                fill_mode="reflect",
                seed=seed,
            ),
            tf.keras.layers.RandomContrast(
                float(augmentation_config.get("contrast_fraction", 0.08)),
                seed=seed,
            ),
        ],
        name="training_only_augmentation",
    )

    def load_image(path, label):
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image.set_shape((None, None, 3))
        image = tf.image.resize_with_pad(image, input_size[1], input_size[0])
        image = tf.cast(image, tf.float32) / 255.0
        if training:
            image = augmentation(image, training=True)
            image = tf.image.random_brightness(
                image,
                float(augmentation_config.get("brightness_fraction", 0.08)),
                seed=seed,
            )
            image = tf.clip_by_value(image, 0.0, 1.0)
        return image, tf.one_hot(label, len(CLASS_NAMES))

    return dataset.map(load_image, num_parallel_calls=tf.data.AUTOTUNE).batch(batch_size).prefetch(tf.data.AUTOTUNE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_type_training.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow is not installed. Install ml/requirements.txt before training.")
        return 1
    from src.dataset import read_manifest, validate_dataset

    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not manifest.is_file():
        print("A validated, licensed dataset manifest is required before training.")
        return 1
    rows = read_manifest(manifest)
    data_root = ML_ROOT / "data"
    validation_report = validate_dataset(rows, data_root)
    if not validation_report["valid"]:
        print("Dataset validation failed. Run scripts/validate_dataset.py for details.")
        return 1
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    if not train_rows or not validation_rows:
        print("Training and validation splits must both contain data.")
        return 1

    seed = int(config["seed"])
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    input_shape = (config["input"]["height"], config["input"]["width"], config["input"]["channels"])
    batch_size = int(config["training"]["batch_size"])
    training_counts = {
        label: sum(row["skin_type_label"] == label for row in train_rows)
        for label in CLASS_NAMES
    }
    if any(count == 0 for count in training_counts.values()):
        print("Every class must be represented in the training split.")
        return 1
    class_weights = {
        index: len(train_rows) / (len(CLASS_NAMES) * training_counts[label])
        for index, label in enumerate(CLASS_NAMES)
    }
    train_data = build_dataset(
        train_rows,
        data_root,
        input_shape[:2][::-1],
        batch_size,
        True,
        seed,
        config.get("augmentation"),
    )
    validation_data = build_dataset(validation_rows, data_root, input_shape[:2][::-1], batch_size, False, seed)
    output = ML_ROOT / config["model"]["output_directory"]
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "best_skin_type_model.keras"
    history_path = output / "training_history.csv"
    history_path.unlink(missing_ok=True)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=config["training"]["early_stopping_patience"], restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=2),
        tf.keras.callbacks.CSVLogger(history_path, append=True),
        tf.keras.callbacks.TensorBoard(log_dir=output / "tensorboard"),
    ]
    model = build_skin_type_model(input_shape, len(CLASS_NAMES), config["training"]["dropout_rate"], pretrained_weights=config["model"]["pretrained_weights"])
    model.compile(optimizer=tf.keras.optimizers.Adam(config["training"]["initial_learning_rate"]), loss="categorical_crossentropy", metrics=["accuracy"])
    model.fit(
        train_data,
        validation_data=validation_data,
        epochs=config["training"]["feature_extraction_epochs"],
        callbacks=callbacks,
        class_weight=class_weights,
    )
    enable_upper_layer_fine_tuning(model, config["training"]["fine_tune_layers"])
    model.compile(optimizer=tf.keras.optimizers.Adam(config["training"]["fine_tuning_learning_rate"]), loss="categorical_crossentropy", metrics=["accuracy"])
    model.fit(
        train_data,
        validation_data=validation_data,
        epochs=config["training"]["fine_tuning_epochs"],
        callbacks=callbacks,
        class_weight=class_weights,
    )
    print(f"Best validation checkpoint: {checkpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

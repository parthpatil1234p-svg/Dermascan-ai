import argparse
import random
import sys
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from src.concern_dataset import (
    calculate_positive_weights,
    read_concern_manifest,
    targets_and_mask,
    validate_concern_dataset,
)
from src.concern_labels import CONCERN_LABELS
from src.concern_model import (
    build_skin_concern_model,
    enable_concern_fine_tuning,
    weighted_masked_binary_crossentropy,
)
from src.utils import load_config, write_json


def concern_augmentation_policy(config):
    values = config.get("augmentation", {})
    return {
        "horizontal_flip": bool(values.get("horizontal_flip", True)),
        "rotation_degrees": float(values.get("rotation_degrees", 8)),
        "translation_fraction": float(values.get("translation_fraction", 0.05)),
        "zoom_fraction": float(values.get("zoom_fraction", 0.10)),
        "brightness_fraction": float(values.get("brightness_fraction", 0.08)),
        "contrast_fraction": float(values.get("contrast_fraction", 0.08)),
    }


def build_concern_dataset(rows, data_root, config, training):
    import tensorflow as tf

    targets, mask = targets_and_mask(rows)
    encoded = np.where(mask > 0, targets, -1.0).astype(np.float32)
    paths = [str(data_root / row["relative_path"]) for row in rows]
    dataset = tf.data.Dataset.from_tensor_slices((paths, encoded))
    if training:
        dataset = dataset.shuffle(len(rows), seed=config["seed"], reshuffle_each_iteration=True)
    augmentation_config = concern_augmentation_policy(config)
    augmentation_layers = []
    if augmentation_config["horizontal_flip"]:
        augmentation_layers.append(
            tf.keras.layers.RandomFlip("horizontal", seed=config["seed"])
        )
    augmentation_layers.extend(
        [
            tf.keras.layers.RandomRotation(augmentation_config["rotation_degrees"] / 360.0, fill_mode="reflect", seed=config["seed"]),
            tf.keras.layers.RandomTranslation(augmentation_config["translation_fraction"], augmentation_config["translation_fraction"], fill_mode="reflect", seed=config["seed"]),
            tf.keras.layers.RandomZoom(augmentation_config["zoom_fraction"], fill_mode="reflect", seed=config["seed"]),
            tf.keras.layers.RandomContrast(augmentation_config["contrast_fraction"], seed=config["seed"]),
        ]
    )
    augmentation = tf.keras.Sequential(augmentation_layers)

    def load_image(path, labels):
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image.set_shape((None, None, 3))
        image = tf.image.resize_with_pad(image, config["input"]["height"], config["input"]["width"])
        image = tf.cast(image, tf.float32) / 255.0
        if training:
            image = augmentation(image, training=True)
            image = tf.image.random_brightness(image, augmentation_config["brightness_fraction"], seed=config["seed"])
            image = tf.clip_by_value(image, 0.0, 1.0)
        return image, labels

    return dataset.map(load_image, num_parallel_calls=tf.data.AUTOTUNE).batch(config["training"]["batch_size"]).prefetch(tf.data.AUTOTUNE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_concern_training.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow is not installed. Install ml/requirements.txt before training.")
        return 1
    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not manifest.is_file():
        print("A validated, licensed concern dataset is required before training.")
        return 1
    rows = read_concern_manifest(manifest)
    data_root = ML_ROOT / "data/concern_dataset"
    if not validate_concern_dataset(rows, data_root)["valid"]:
        print("Concern dataset validation failed.")
        return 1
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    if not train_rows or not validation_rows:
        print("Training and validation splits are both required.")
        return 1
    train_targets, train_mask = targets_and_mask(train_rows)
    positive_weights = calculate_positive_weights(train_targets, train_mask)
    if any(train_mask[:, index].sum() == 0 or train_targets[:, index].sum() == 0 for index in range(len(CONCERN_LABELS))):
        print("Every concern requires known positive training examples.")
        return 1

    random.seed(config["seed"])
    np.random.seed(config["seed"])
    tf.random.set_seed(config["seed"])
    output = ML_ROOT / config["model"]["output_directory"]
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "best_skin_concern_model.keras"
    history = output / "training_history.csv"
    history.unlink(missing_ok=True)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=config["training"]["early_stopping_patience"], restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=2),
        tf.keras.callbacks.CSVLogger(history, append=True),
        tf.keras.callbacks.TensorBoard(log_dir=output / "tensorboard"),
    ]
    input_shape = (config["input"]["height"], config["input"]["width"], config["input"]["channels"])
    model = build_skin_concern_model(input_shape, len(CONCERN_LABELS), config["model"]["dropout_rate"], pretrained_weights=config["model"]["pretrained_weights"], seed=config["seed"])
    loss = weighted_masked_binary_crossentropy(positive_weights)
    train_data = build_concern_dataset(train_rows, data_root, config, True)
    validation_data = build_concern_dataset(validation_rows, data_root, config, False)
    model.compile(optimizer=tf.keras.optimizers.Adam(config["training"]["initial_learning_rate"]), loss=loss)
    model.fit(train_data, validation_data=validation_data, epochs=config["training"]["feature_extraction_epochs"], callbacks=callbacks)
    enable_concern_fine_tuning(model, config["training"]["fine_tune_layers"])
    model.compile(optimizer=tf.keras.optimizers.Adam(config["training"]["fine_tuning_learning_rate"]), loss=loss)
    model.fit(train_data, validation_data=validation_data, epochs=config["training"]["fine_tuning_epochs"], callbacks=callbacks)
    write_json(output / "positive_class_weights.json", dict(zip(CONCERN_LABELS, map(float, positive_weights), strict=True)))
    print(f"Best validation checkpoint: {checkpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from typing import Any


def build_skin_concern_model(
    input_shape: tuple[int, int, int],
    number_of_labels: int,
    dropout_rate: float,
    *,
    pretrained_weights: str | None = "imagenet",
    seed: int = 42,
) -> Any:
    if len(input_shape) != 3 or input_shape[2] != 3:
        raise ValueError("MobileNetV2 requires an RGB input shape.")
    if number_of_labels < 1:
        raise ValueError("At least one concern output is required.")
    import tensorflow as tf

    tf.keras.utils.set_random_seed(seed)
    base = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights=pretrained_weights,
    )
    base.trainable = False
    inputs = tf.keras.Input(shape=input_shape)
    features = base(inputs, training=False)
    features = tf.keras.layers.GlobalAveragePooling2D()(features)
    features = tf.keras.layers.Dropout(dropout_rate, seed=seed)(features)
    outputs = tf.keras.layers.Dense(number_of_labels, activation="sigmoid")(features)
    model = tf.keras.Model(inputs, outputs, name="dermascan_skin_concern_mobilenetv2")
    model.backbone = base
    return model


def enable_concern_fine_tuning(model: Any, layer_count: int) -> None:
    if layer_count < 1:
        raise ValueError("Fine-tuning layer count must be positive.")
    base = model.backbone
    base.trainable = True
    for layer in base.layers[:-layer_count]:
        layer.trainable = False
    for layer in base.layers[-layer_count:]:
        if layer.__class__.__name__ == "BatchNormalization":
            layer.trainable = False


def weighted_masked_binary_crossentropy(positive_weights: Any):
    import tensorflow as tf

    weights = tf.constant(positive_weights, dtype=tf.float32)

    def loss(y_true, y_pred):
        mask = tf.cast(y_true >= 0.0, tf.float32)
        targets = tf.clip_by_value(y_true, 0.0, 1.0)
        predictions = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)
        values = -(
            weights * targets * tf.math.log(predictions)
            + (1.0 - targets) * tf.math.log(1.0 - predictions)
        )
        return tf.reduce_sum(values * mask) / tf.maximum(tf.reduce_sum(mask), 1.0)

    return loss

from typing import Any


def build_skin_type_model(
    input_shape: tuple[int, int, int],
    number_of_classes: int,
    dropout_rate: float,
    *,
    pretrained_weights: str = "imagenet",
) -> Any:
    if len(input_shape) != 3 or input_shape[2] != 3:
        raise ValueError("MobileNetV2 requires an RGB input shape.")
    if number_of_classes < 2:
        raise ValueError("At least two output classes are required.")
    import tensorflow as tf

    base = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights=pretrained_weights,
    )
    base.trainable = False
    inputs = tf.keras.Input(shape=input_shape)
    features = base(inputs, training=False)
    features = tf.keras.layers.GlobalAveragePooling2D()(features)
    features = tf.keras.layers.Dropout(dropout_rate)(features)
    outputs = tf.keras.layers.Dense(number_of_classes, activation="softmax")(features)
    model = tf.keras.Model(inputs, outputs, name="dermascan_skin_type_mobilenetv2")
    model.backbone = base
    return model


def enable_upper_layer_fine_tuning(model: Any, layer_count: int) -> None:
    base = model.backbone
    base.trainable = True
    for layer in base.layers[:-layer_count]:
        layer.trainable = False
    for layer in base.layers[-layer_count:]:
        if layer.__class__.__name__ == "BatchNormalization":
            layer.trainable = False

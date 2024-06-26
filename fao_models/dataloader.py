import tensorflow as tf
import os


def _parse_function(proto):
    # Define the parsing schema
    feature_description = {
        "image": tf.io.FixedLenFeature([], tf.string),
        "label": tf.io.FixedLenFeature([], tf.string),
    }
    # Parse the input `tf.train.Example` proto using the schema
    example = tf.io.parse_single_example(proto, feature_description)
    image = tf.io.parse_tensor(example["image"], out_type=tf.float32)
    label = tf.io.parse_tensor(example["label"], out_type=tf.int64)
    image.set_shape([32, 32, 4])  # Set the shape explicitly if not already defined
    label.set_shape([])  # For scalar labels
    return image, label


def load_dataset_from_tfrecords(
    tfrecord_dir, batch_size=32, buffer_size=100, seed=4, shuffle: bool = True
):

    pattern = tfrecord_dir + "/*.tfrecord.gz"
    files = tf.data.Dataset.list_files(pattern, shuffle=False)
    dataset = files.interleave(
        lambda x: tf.data.TFRecordDataset(x, compression_type="GZIP"),
        cycle_length=tf.data.AUTOTUNE,
        block_length=1,
    )
    dataset = dataset.map(_parse_function, num_parallel_calls=tf.data.AUTOTUNE).batch(
        batch_size, drop_remainder=True
    )
    if shuffle:
        dataset = dataset.shuffle(buffer_size=buffer_size, seed=seed)
    return dataset


def split_dataset(
    dataset, total_examples, test_split=0.2, batch_size=32, val_split=None
):
    if val_split:
        val_size = int(total_examples * val_split)
        test_size = int(total_examples * test_split)
        train_size = total_examples - test_size - val_size

        # Calculate the number of batches for train and test sets
        val_batches = val_size // batch_size
        test_batches = test_size // batch_size
        train_batches = train_size // batch_size

        val_dataset = dataset.take(val_batches).prefetch(tf.data.AUTOTUNE)
        test_dataset = (
            dataset.skip(val_batches).take(test_batches).prefetch(tf.data.AUTOTUNE)
        )
        train_dataset = (
            dataset.skip(val_batches + test_batches)
            .take(train_batches)
            .prefetch(tf.data.AUTOTUNE)
        )

        return train_dataset, test_dataset, val_dataset

    else:
        test_size = int(total_examples * test_split)
        train_size = total_examples - test_size

        # Calculate the number of batches for train and test sets
        train_batches = train_size // batch_size
        test_batches = test_size // batch_size

        train_dataset = dataset.take(train_batches).prefetch(tf.data.AUTOTUNE)
        test_dataset = (
            dataset.skip(train_batches).take(test_batches).prefetch(tf.data.AUTOTUNE)
        )

        return train_dataset, test_dataset

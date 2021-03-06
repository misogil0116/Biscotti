import argparse
import os
import numpy as np

import keras.backend as K
from keras.optimizers import Adam

from keras.utils import generic_utils
from keras.callbacks import ModelCheckpoint

import nets


def load_img_and_dct_data(dataset_path):
    files = os.listdir(dataset_path)
    X = np.zeros((len(files), 224, 224, 3))
    y = np.zeros((len(files), 224, 224, 3))

    for i, file in enumerate(files):
        data = np.load(dataset_path + "/" + file)
        img, dct = data[:, :, :3], data[:, :, 3:]
        X[i] = img
        y[i] = dct
    
    threshold = int(X.shape[0]*0.9)
    X_train, X_valid = X[:threshold], X[threshold:]
    y_train, y_valid = y[:threshold], y[threshold:]
    return X_train, X_valid, y_train, y_valid


def extract_patches(X, patch_size):
    list_X = []
    list_row_idx = [(i*patch_size, (i+1)*patch_size) for i in range(X.shape[1] // patch_size)]
    list_col_idx = [(i*patch_size, (i+1)*patch_size) for i in range(X.shape[2] // patch_size)]
    for row_idx in list_row_idx:
        for col_idx in list_col_idx:
            list_X.append(X[:, row_idx[0]:row_idx[1], col_idx[0]:col_idx[1], :])
    return list_X


def get_disc_batch(X_dct, X_input, generator_model, batch_counter, patch_size):
    if batch_counter % 2 == 0:
        X_disc = generator_model.predict(X_input)
        y_disc = np.zeros((X_disc.shape[0], 2), dtype=np.uint8)
    else:
        X_disc = X_dct
        y_disc = np.zeros((X_disc.shape[0], 2), dtype=np.uint8)
    
    X_disc = extract_patches(X_disc, patch_size)
    return X_disc, y_disc

def get_train_iterator(perm, images, dcts, batch_size):
    perm_batch = [perm[i:i+batch_size] for i in range(0, perm.shape[0], batch_size)]
    for pb in perm_batch:
        yield dcts[pb], images[pb]

def load_train_data_on_batch(dataset_path, perm, train_files, batch_size):
    X = np.zeros((batch_size, 224, 224, 3))
    y = np.zeros((batch_size, 224, 224, 3))
    for i, p_num in enumerate(perm):
        data = np.load(dataset_path + "/" + train_files[p_num])
        img, dct = data[:, :, :3], data[:, :, 3:]
        X[i] = img
        y[i] = dct
    return y, X


def load_validation_dataset(dataset_path, test_files):
    X = np.zeros((len(test_files), 224, 224, 3))
    y = np.zeros((len(test_files), 224, 224, 3))
    for i, test_file in enumerate(test_files):
        data = np.load(dataset_path + "/" + test_file)
        img, dct = data[:, :, :3], data[:, :, 3:]
        X[i] = img
        y[i] = dct
    return X, y

def train(args):
    output = args.outputfile
    if not os.path.exists("./figure"):
        os.mkdir("./figure")

    # image_shape
    image_shape = args.train_size

    # load data
    # images, images_val, dcts,  dcts_val = load_img_and_dct_data(args.datasetpath)
    # print("train_image shape: ", images.shape)
    # print("train_dct shape: ", dcts.shape)
    # print("validation image shape: ", images_val.shape)
    # print("validation dct shape: ", dcts_val.shape)
    # img_shape = images.shape[-3:]
    data_files = sorted(os.listdir(args.datasetpath))
    threshold = int(len(data_files)*0.9)
    train_files = data_files[:threshold]
    test_files = data_files[threshold:]
    X_valid, y_valid = load_validation_dataset(args.dataset_path, test_files)
    batch_size = args.batch_size

    patch_num = (image_shape // args.patch_size) * (image_shape // args.patch_size)
    img_shape = (args.image_shape, args.image_shape, 3)
    disc_img_shape = (args.patch_size, args.patch_size, 3)

    # set optimizer
    opt_dcgan = Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
    opt_discriminator = Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, epsilon=1e-08)

    # load generator model
    generator_model = nets.get_generator(img_shape)
    # load discriminator
    discriminator_model = nets.get_discriminator(img_shape, disc_img_shape, patch_num)
    generator_model.compile(loss='binary_crossentropy', optimizer=opt_discriminator, metrics=['accuracy'])
    discriminator_model.trainable = False
    
    dcgan_model = nets.get_GAN(generator_model, discriminator_model, img_shape, args.patch_size)

    loss = ['binary_crossentropy', 'binary_crossentropy']
    loss_weights = [1E1, 1]
    dcgan_model.compile(loss=loss, loss_weights=loss_weights, optimizer=opt_dcgan)

    discriminator_model.trainable = True
    discriminator_model.compile(loss="binary_crossentropy", optimizer=opt_discriminator)

    print("start training...")
    # TODO: permごとにtrainから読み込むことで学習させるようにソースコードを変更する
    for epoch in range(args.epoch):
        perm = np.random.permutation(len(train_files))
        perm_batch = [perm[i:i+batch_size] for i in range(0, len(train_files), batch_size)]
        b_it = 0
        progbar = generic_utils.Progbar(len(train_files))

        # ここからバッチごとに処理を行う
        for X_dct_batch, X_input_batch in load_train_data_on_batch(args.dataset_path, perm_batch[b_it], train_files, batch_size):
            b_it += 1

            X_disc, y_disc = get_disc_batch(X_dct_batch, X_input_batch, generator_model, b_it, args.patch_size)
            raw_disc, _ = get_disc_batch(X_input_batch, X_input_batch, generator_model, 1, args.patch_size)
            disc_input = X_disc + raw_disc

            # update discriminator
            disc_loss = discriminator_model.train_on_batch(disc_input, y_disc)

            # 変更不可欠
            idx = np.random.choice(len(train_files), args.batch_size)
            
            # X_gen_target, X_gen = dcts[idx], images[idx]
            X_gen_target, X_gen = load_train_data_on_batch(args.dataset_path, idx, train_files, batch_size)
            y_gen = np.zeros((X_gen.shape[0], 2), dtype=np.uint8)
            y_gen[:, 1] = 1

            # Freeze the discriminator
            discriminator_model.trainable = False
            gen_loss = dcgan_model.train_on_batch(X_gen, [X_gen_target, y_gen])
            discriminator_model.trainable = True

            progbar.add(args.batch_size, values=[
                ("D logloss", disc_loss),
                ("G loss1", gen_loss[0]),
                ("G L1", gen_loss[1]),
                ("G logloss", gen_loss[2])
            ])
        
        # save weight
        generator_model.save_weights(args.outputfile + "/generator_%d.h5"%epoch)

def main():
    parser = argparse.ArgumentParser(description="Training pix2pix")
    parser.add_argument("--datasetpath", '-d', type=str, required=True)
    parser.add_argument("--outputfile", "-o", type=str, required=True)
    parser.add_argument("--patch_size", "-p", type=int, default=112)
    parser.add_argument("--batch_size", "-b", type=int, default=5)
    parser.add_argument("--epoch", type=int, default=400)
    parser.add_argument("--train_size", "-t", type=int, default=224)
    args = parser.parse_args()
    K.set_image_data_format("channels_last")

    train(args)

if __name__ == "__main__":
    main()

import argparse
import importlib
import util.data
import util.display
import numpy as np
import os
import torch

parser = argparse.ArgumentParser()
parser.add_argument('--data_path', default='data', help='path to data directory')
parser.add_argument('--gpu_id', type=int, default=0, help='GPU ID')
parser.add_argument('--load_path', help='path to trained model')
parser.add_argument('--model_module', default='ttf_model', help='name of the model module')
parser.add_argument('--n_images', type=int, help='max number of images to test')
parser.add_argument('--save_each_slice', action='store_true', default=False, help='save each z slice of test image')
parser.add_argument('--save_images', action='store_true', default=False, help='save test image results')
parser.add_argument('--use_train_set', action='store_true', default=False, help='view predictions on training set images')
opts = parser.parse_args()

model_module = importlib.import_module('model_modules.'  + opts.model_module)

def test_display(model, data):
    y_pred = np.zeros((1, 1) + data.get_dims_chunk(), dtype=np.float32)
    for i, (x_test, y_true) in enumerate(data):
        if model is not None:
            y_pred[:] = model.predict(x_test)
        util.display.display_visual_eval_images(x_test, y_true, y_pred, z_selector='strongest_in_target')
        if opts.save_images:
            name_model = os.path.basename(opts.load_path).split('.')[0]
            img_trans = x_test[0, 0, ].astype(np.float32)
            img_dna = y_true[0, 0, ].astype(np.float32)
            img_pred = y_pred[0, 0, ]
            name_pre = 'test_output/{:s}_test_{:02d}_'.format(name_model, i)
            name_post = '.tif'
            name_trans = name_pre + 'trans' + name_post
            name_dna = name_pre + 'dna' + name_post
            name_pred = name_pre + 'prediction' + name_post
            util.save_img_np(img_trans, name_trans)
            util.save_img_np(img_dna, name_dna)
            util.save_img_np(img_pred, name_pred)
        if opts.save_each_slice:
            dir_save = 'presentation/' + ('test' if not opts.use_train_set else 'train') + '_{:02d}'.format(i)
            util.display.save_image_stacks(dir_save, (x_test, y_true, y_pred))
        if (opts.n_images is not None) and (i == (opts.n_images - 1)):
            break
    
def main():
    torch.cuda.set_device(opts.gpu_id)
    print('on GPU:', torch.cuda.current_device())
    
    if opts.use_train_set:
        print('*** Using training set ***')
    train_select = opts.use_train_set

    # load test dataset
    dataset = util.data.DataSet(opts.data_path, train_select=train_select)
    print(dataset)

    # dims_chunk = (32, 224, 224)
    dims_chunk = (32, 208, 208)
    dims_pin = (0, 0, 0)
    data_test = util.data.TestImgDataProvider(dataset, dims_chunk=dims_chunk, dims_pin=dims_pin)
    
    # load model
    model = None
    if opts.load_path is not None:
        model = model_module.Model(load_path=opts.load_path)
    print(model)
    test_display(model, data_test)

if __name__ == '__main__':
    main()

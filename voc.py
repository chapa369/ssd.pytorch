# voc.py
"""VOC Dataset Classes

Original author: Francisco Massa
https://github.com/fmassa/vision/blob/voc_dataset/torchvision/datasets/voc.py

Ellis Brown
"""
import os
import os.path
import sys

# from config import VOCroot

# import torch
import torch.utils.data as data
from PIL import Image, ImageDraw
import collections
if sys.version_info[0] == 2:
    import xml.etree.cElementTree as ET
else:
    import xml.etree.ElementTree as ET

VOC_CLASSES = ('__background__',  # always index 0
               'aeroplane', 'bicycle', 'bird', 'boat',
               'bottle', 'bus', 'car', 'cat', 'chair',
               'cow', 'diningtable', 'dog', 'horse',
               'motorbike', 'person', 'pottedplant',
               'sheep', 'sofa', 'train', 'tvmonitor')

# for making bounding boxes pretty
COLORS = ((255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128),
          (0, 255, 255, 128), (255, 0, 255, 128), (255, 255, 0, 128))


class VOCSegmentation(data.Dataset):
    """VOC Segmentation Dataset Object

    NOTE: need to address https://github.com/pytorch/vision/issues/9

    Arguments:
        root (string): filepath to VOCdevkit folder.
        image_set (string): imageset to use (eg. 'train', 'val', 'test')
        input_transform (function): transformation to perform on input img
        target_transform (function): transformation to perform on target img
        dataset_name (string): the name of the dataset to load
            default: VOC2007
    """

    def __init__(self, root, image_set, input_transform=None, target_transform=None,
                 dataset_name='VOC2007'):
        self.root = root
        self.image_set = image_set
        self.input_transform = input_transform
        self.target_transform = target_transform

        self._annopath = os.path.join(
            self.root, dataset_name, 'SegmentationClass', '%s.png')
        self._imgpath = os.path.join(
            self.root, dataset_name, 'JPEGImages', '%s.jpg')
        self._imgsetpath = os.path.join(
            self.root, dataset_name, 'ImageSets', 'Segmentation', '%s.txt')

        with open(self._imgsetpath % self.image_set) as f:
            self.ids = f.readlines()
        self.ids = [x.strip('\n') for x in self.ids]

    def __getitem__(self, index):
        img_id = self.ids[index]

        target = Image.open(self._annopath % img_id).convert('RGB')
        img = Image.open(self._imgpath % img_id).convert('RGB')

        if self.input_transform is not None:
            img = self.input_transform(img)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def __len__(self):
        return len(self.ids)


class AnnotationTransform(object):
    """Transforms a VOC annotation into a more usable format
    Initilized with a dictionary lookup of classnames to indexes

    Arguments:
        class_to_ind (dict): {<classname> : <classindex>}
            default: alphabetic indexing of VOC's 20 classes
        keep_difficult (bool): whether or not to keep difficult instances
            defualt: False
    """

    def __init__(self, class_to_ind=None, keep_difficult=False):
        self.class_to_ind = class_to_ind or dict(
            zip(VOC_CLASSES, range(len(VOC_CLASSES))))
        self.keep_difficult = keep_difficult

    def __call__(self, target):
        """
        Arguments:
            target (annotation xml) : the target annotation to be made usable
        Returns:
            an array containing [bbox coords, class name] subarrays
        """
        res = []
        for obj in target.iter('object'):
            difficult = int(obj.find('difficult').text) == 1
            if not self.keep_difficult and difficult:
                continue
            #name = obj.find('name').text
            name = obj[0].text.lower().strip()
            #bb = obj.find('bndbox')
            bbox = obj[4]
            # [xmin, ymin, xmax, ymax]
            bndbox = [int(bb.text) - 1 for bb in bbox]

            res += [bndbox + [name]]  # [[xmin, ymin, xmax, ymax], name]

        return res  # [[[xmin, ymin, xmax, ymax], name], ... ]


class VOCDetection(data.Dataset):
    """VOC Detection Dataset Object

    Arguments:
        root (string): filepath to VOCdevkit folder.
        image_set (string): imageset to use (eg. 'train', 'val', 'test')
        transform (function): a function that takes in an image and returns a
            transformed version
        target_transform (function): a function that takes in the target and
            transforms it
            (eg. take in caption string, return tensor of word indices)
        dataset_name (string): the name of the dataset to load
            default: VOC2007
    """

    def __init__(self, root, image_set, transform=None, target_transform=None,
                 dataset_name='VOC2007'):
        self.root = root
        self.image_set = image_set
        self.transform = transform
        self.target_transform = target_transform

        self._annopath = os.path.join(
            self.root, dataset_name, 'Annotations', '%s.xml')
        self._imgpath = os.path.join(
            self.root, dataset_name, 'JPEGImages', '%s.jpg')
        self._imgsetpath = os.path.join(
            self.root, dataset_name, 'ImageSets', 'Main', '%s.txt')

        with open(self._imgsetpath % self.image_set) as f:
            self.ids = f.readlines()
        self.ids = [x.strip('\n') for x in self.ids]

    def __getitem__(self, index):
        img_id = self.ids[index]

        target = ET.parse(self._annopath % img_id).getroot()
        img = Image.open(self._imgpath % img_id).convert('RGB')

        if self.transform is not None:
            img = self.transform(img)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def __len__(self):
        return len(self.ids)

    def show(self, index):
        '''Shows an image with its bounding box overlaid

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to show
        '''
        img_id = self.ids[index]
        target = ET.parse(self._annopath % img_id).getroot()
        img = Image.open(self._imgpath % img_id).convert('RGB')
        draw = ImageDraw.Draw(img)
        i = 0
        for obj in target.iter('object'):
            bbox = obj.find('bndbox')
            bndbox = [int(bb.text) - 1 for bb in bbox]  # [x1,y1,x2,y2]
            draw.rectangle(bndbox, outline=COLORS[i % len(COLORS)])
            draw.text(bndbox[:2], obj.find('name').text,
                      fill=COLORS[(i + 3) % len(COLORS)])
            i += 1
        img.show()

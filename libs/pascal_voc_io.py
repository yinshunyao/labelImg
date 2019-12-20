#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
from libs.constants import DEFAULT_ENCODING
from libs.ustr import ustr
from libs.label_manager import LabelManager, INTER_FLAG, VALUE_FLAG


XML_EXT = '.xml'
ENCODE_METHOD = DEFAULT_ENCODING

# 增加特殊的标注框，指定图片属性
attr_flag_example = {
    "{不能做样本}": "nosample",
    "{全部正常}" : "allnormal",
    "[红框]": "red",    # 默认well
    "[长宽比改变]": "change",
    # "正常": "well",
    "[人为因素]": "human",
    "[成像污染]": "contaminate",
}


class PascalVocWriter:

    def __init__(self, foldername, filename, imgSize, label_manager: LabelManager, databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False
        # 标签管理转换器
        self.label_manager = label_manager

    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        root = etree.fromstring(rough_string)
        return etree.tostring(root, pretty_print=True, encoding=ENCODE_METHOD).replace("  ".encode(), "\t".encode())
        # minidom does not support UTF-8
        '''reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t", encoding=ENCODE_METHOD)'''

    def genXML(self):
        """
            Return XML root
        """
        # Check conditions
        if self.filename is None or \
                self.foldername is None or \
                self.imgSize is None:
            return None

        top = Element('annotation')
        if self.verified:
            top.set('verified', 'yes')

        # 其他自由属性设置
        for k, v in self.label_manager.attr_flag.items():
            k_node = SubElement(top, k)
            flag = SubElement(k_node, "flag")
            if not v:
                flag.text = "false"
                continue

            flag.text = "true"
            bndbox = SubElement(k_node, 'bndbox')
            xmin = SubElement(bndbox, 'xmin')
            xmin.text = str(v['xmin'])
            ymin = SubElement(bndbox, 'ymin')
            ymin.text = str(v['ymin'])
            xmax = SubElement(bndbox, 'xmax')
            xmax.text = str(v['xmax'])
            ymax = SubElement(bndbox, 'ymax')
            ymax.text = str(v['ymax'])


        folder = SubElement(top, 'folder')
        folder.text = self.foldername

        filename = SubElement(top, 'filename')
        filename.text = self.filename

        if self.localImgPath is not None:
            localImgPath = SubElement(top, 'path')
            localImgPath.text = self.localImgPath

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.databaseSrc

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])
        if len(self.imgSize) == 3:
            depth.text = str(self.imgSize[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top

    def add_label(self, xmin, ymin, xmax, ymax, name, difficult):
        """
        新的标签处理
        :param xmin:
        :param ymin:
        :param xmax:
        :param ymax:
        :param name:
        :param difficult:
        :return:
        """
        self.label_manager.new_attr_or_bbox(xmin, ymin, xmax, ymax, name, difficult)

    def appendObjects(self, top):
        for each_object in self.label_manager.bbox_flag:
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            name.text = ustr(each_object['name'])
            pose = SubElement(object_item, 'pose')
            pose.text = "Unspecified"
            truncated = SubElement(object_item, 'truncated')
            if int(float(each_object['ymax'])) == int(float(self.imgSize[0])) or (int(float(each_object['ymin']))== 1):
                truncated.text = "1" # max == height or min
            elif (int(float(each_object['xmax']))==int(float(self.imgSize[1]))) or (int(float(each_object['xmin']))== 1):
                truncated.text = "1" # max == width or min
            else:
                truncated.text = "0"
            difficult = SubElement(object_item, 'difficult')
            difficult.text = str( bool(each_object['difficult']) & 1 )
            # value判断
            if each_object.get("value"):
                value = SubElement(object_item, 'value')
                value.text = str(each_object.get("value"))


            bndbox = SubElement(object_item, 'bndbox')
            xmin = SubElement(bndbox, 'xmin')
            xmin.text = str(each_object['xmin'])
            ymin = SubElement(bndbox, 'ymin')
            ymin.text = str(each_object['ymin'])
            xmax = SubElement(bndbox, 'xmax')
            xmax.text = str(each_object['xmax'])
            ymax = SubElement(bndbox, 'ymax')
            ymax.text = str(each_object['ymax'])

    def save(self, targetFile=None):
        root = self.genXML()
        self.appendObjects(root)
        out_file = None
        if targetFile is None:
            out_file = codecs.open(
                self.filename + XML_EXT, 'w', encoding=ENCODE_METHOD)
        else:
            out_file = codecs.open(targetFile, 'w', encoding=ENCODE_METHOD)

        prettifyResult = self.prettify(root)
        out_file.write(prettifyResult.decode('utf8'))
        out_file.close()


class PascalVocReader:

    def __init__(self, filepath, label_manager: LabelManager, **kwargs):
        """
        读取xml
        :param filepath:
        :param label_manager:
        :param kwargs:
        """
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.filepath = filepath
        self.label_manager = label_manager
        self.verified = False
        try:
            self.parseXML()
        except Exception as e:
            print("标签加载异常：{}".format(e))

    def getShapes(self):
        return self.shapes

    def addShape(self, label, bndbox, difficult):
        xmin = int(float(bndbox.find('xmin').text))
        ymin = int(float(bndbox.find('ymin').text))
        xmax = int(float(bndbox.find('xmax').text))
        ymax = int(float(bndbox.find('ymax').text))
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((label, points, None, None, difficult))

    def parseXML(self):
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding=ENCODE_METHOD)
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        filename = xmltree.find('filename').text
        try:
            verified = xmltree.attrib['verified']
            if verified == 'yes':
                self.verified = True
        except KeyError:
            self.verified = False

        # 加载属性，并生成特殊的标记框
        for k in self.label_manager.attr_key_list:
            try:
                attr = xmltree.find(k)
                # 如果标记过，则获取边框
                if attr.find('flag').text == "true":
                    # 英文转中文
                    self.addShape(self.label_manager.get_attr_name(k), attr.find("bndbox"), False)
            except:
                # xml标签中没有找到，默认为空,false
                pass

        for object_iter in xmltree.findall('object'):
            bndbox = object_iter.find("bndbox")
            label = object_iter.find('name').text
            name = self.label_manager.get_bbox_name(label)
            # Add chris
            difficult = False
            if object_iter.find('difficult') is not None:
                difficult = bool(int(object_iter.find('difficult').text))

            # 可选的value值
            value = None
            if INTER_FLAG in name and object_iter.find(VALUE_FLAG) is not None:
                value = str(object_iter.find(VALUE_FLAG).text)
            if value:
                name += value

            self.addShape(name, bndbox, difficult)
        return True

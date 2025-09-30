import sys
import os
import json
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog, 
    QTextEdit, QSlider, QComboBox, QSpinBox, QColorDialog, QCheckBox,
    QGroupBox, QTabWidget, QLineEdit, QMessageBox, QSplitter, QFrame,
    QInputDialog
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen, QIcon
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PIL import Image, ImageDraw, ImageFont

class WatermarkerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化变量
        self.images = []
        self.image_paths = []
        self.current_image_index = -1
        self.watermark_position = QPoint(50, 50)  # 确保初始化为QPoint类型
        self.dragging = False
        
        self.initUI()
        self.loadSettings()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('Watermarker2')
        self.setGeometry(100, 100, 1200, 800)
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧面板（图片列表）
        left_panel = QWidget()
        left_panel.setMaximumWidth(200)
        left_layout = QVBoxLayout(left_panel)
        
        # 导入按钮
        import_button = QPushButton('导入图片')
        import_button.clicked.connect(self.importImages)
        left_layout.addWidget(import_button)
        
        # 批量导入按钮
        batch_import_button = QPushButton('文件夹导入')
        batch_import_button.clicked.connect(self.batchImportImages)
        left_layout.addWidget(batch_import_button)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(150, 100))
        self.image_list.setUniformItemSizes(True)
        self.image_list.setSelectionMode(QListWidget.SingleSelection)
        self.image_list.itemClicked.connect(self.onImageSelected)
        left_layout.addWidget(self.image_list)
        
        # 创建中间面板（预览区域）
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 预览标签
        self.preview_label = QLabel('预览区域')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        center_layout.addWidget(self.preview_label)
        
        # 导出按钮
        export_button = QPushButton('导出图片')
        export_button.clicked.connect(self.exportImage)
        center_layout.addWidget(export_button)
        
        # 创建右侧面板（设置区域）
        right_panel = QWidget()
        right_panel.setMaximumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # 文本水印标签页
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        
        # 文本内容
        text_group = QGroupBox('文本内容')
        text_group_layout = QVBoxLayout(text_group)
        self.text_content = QTextEdit()
        self.text_content.setPlaceholderText('请输入水印文本')
        self.text_content.textChanged.connect(self.updatePreview)
        text_group_layout.addWidget(self.text_content)
        text_layout.addWidget(text_group)
        
        # 字体设置
        font_group = QGroupBox('字体设置')
        font_group_layout = QVBoxLayout(font_group)
        
        # 字体大小
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel('字体大小:'))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 120)
        self.font_size.setValue(32)
        self.font_size.valueChanged.connect(self.updatePreview)
        font_size_layout.addWidget(self.font_size)
        font_group_layout.addLayout(font_size_layout)
        
        # 字体颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel('字体颜色:'))
        self.color_button = QPushButton('选择颜色')
        self.color_button.clicked.connect(self.selectColor)
        self.font_color = '#FFFFFF'  # 默认白色
        self.color_button.setStyleSheet('background-color: #FFFFFF; color: black; border: 1px solid #ccc;')
        color_layout.addWidget(self.color_button)
        font_group_layout.addLayout(color_layout)
        
        # 透明度
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel('透明度:'))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(1, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.updatePreview)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(QLabel('50%'))
        self.opacity_slider.valueChanged.connect(lambda value: opacity_layout.itemAt(2).widget().setText(f'{value}%'))
        font_group_layout.addLayout(opacity_layout)
        
        # 粗体斜体
        style_layout = QHBoxLayout()
        self.bold_check = QCheckBox('粗体')
        self.bold_check.stateChanged.connect(self.updatePreview)
        self.italic_check = QCheckBox('斜体')
        self.italic_check.stateChanged.connect(self.updatePreview)
        style_layout.addWidget(self.bold_check)
        style_layout.addWidget(self.italic_check)
        font_group_layout.addLayout(style_layout)
        
        text_layout.addWidget(font_group)
        
        # 位置设置
        position_group = QGroupBox('位置设置')
        position_group_layout = QVBoxLayout(position_group)
        
        # 预设位置按钮网格
        position_grid = QWidget()
        position_grid_layout = QGridLayout(position_grid)
        
        # 使用字符串标识符而非固定像素值，这些将在updatePreview中转换为实际位置
        position_ids = [
            ('左上', 'top-left'),
            ('右上', 'top-right'),
            ('左下', 'bottom-left'),
            ('右下', 'bottom-right'),
            ('居中', 'center')
        ]
        
        for i, (text, pos_id) in enumerate(position_ids):
            btn = QPushButton(text)
            btn.setFixedSize(70, 30)
            btn.clicked.connect(lambda checked, p=pos_id: self.setWatermarkPosition(p))
            if i < 3:
                position_grid_layout.addWidget(btn, 0, i)
            else:
                position_grid_layout.addWidget(btn, 1, i-3)
        
        position_group_layout.addWidget(position_grid)
        text_layout.addWidget(position_group)
        
        # 旋转设置
        rotate_layout = QHBoxLayout()
        rotate_layout.addWidget(QLabel('旋转角度:'))
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setRange(0, 359)
        self.rotate_slider.setValue(0)
        self.rotate_slider.valueChanged.connect(self.updatePreview)
        rotate_layout.addWidget(self.rotate_slider)
        rotate_layout.addWidget(QLabel('0°'))
        self.rotate_slider.valueChanged.connect(lambda value: rotate_layout.itemAt(2).widget().setText(f'{value}°'))
        text_layout.addLayout(rotate_layout)
        
        tabs.addTab(text_tab, '文本水印')
        
        # 模板标签页
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        
        # 模板列表
        self.template_list = QListWidget()
        template_layout.addWidget(QLabel('已保存的模板:'))
        template_layout.addWidget(self.template_list)
        
        # 模板操作按钮
        template_buttons = QHBoxLayout()
        save_template_button = QPushButton('保存当前设置')
        save_template_button.clicked.connect(self.saveTemplate)
        load_template_button = QPushButton('加载模板')
        load_template_button.clicked.connect(self.loadTemplate)
        delete_template_button = QPushButton('删除模板')
        delete_template_button.clicked.connect(self.deleteTemplate)
        template_buttons.addWidget(save_template_button)
        template_buttons.addWidget(load_template_button)
        template_buttons.addWidget(delete_template_button)
        template_layout.addLayout(template_buttons)
        
        tabs.addTab(template_tab, '模板管理')
        
        # 导出设置标签页
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('输出格式:'))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['JPEG', 'PNG'])
        format_layout.addWidget(self.format_combo)
        export_layout.addLayout(format_layout)
        
        # 命名规则
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('命名规则:'))
        self.name_combo = QComboBox()
        self.name_combo.addItems(['保留原文件名', '添加前缀', '添加后缀'])
        self.name_combo.currentIndexChanged.connect(self.togglePrefixSuffix)
        name_layout.addWidget(self.name_combo)
        export_layout.addLayout(name_layout)
        
        # 前缀/后缀输入
        self.prefix_suffix_layout = QHBoxLayout()
        self.prefix_suffix_input = QLineEdit()
        self.prefix_suffix_input.setPlaceholderText('请输入前缀/后缀')
        self.prefix_suffix_layout.addWidget(QLabel(':'))
        self.prefix_suffix_layout.addWidget(self.prefix_suffix_input)
        self.prefix_suffix_layout.itemAt(0).widget().hide()  # 初始隐藏标签
        self.prefix_suffix_input.hide()  # 初始隐藏输入框
        export_layout.addLayout(self.prefix_suffix_layout)
        
        # 图片质量（仅JPEG）
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel('图片质量:'))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(QLabel('90%'))
        self.quality_slider.valueChanged.connect(lambda value: quality_layout.itemAt(2).widget().setText(f'{value}%'))
        self.format_combo.currentTextChanged.connect(self.toggleQualitySlider)
        export_layout.addLayout(quality_layout)
        
        # 批量处理按钮
        batch_process_button = QPushButton('批量处理')
        batch_process_button.clicked.connect(self.batchProcess)
        export_layout.addWidget(batch_process_button)
        
        tabs.addTab(export_tab, '导出设置')
        
        right_layout.addWidget(tabs)
        
        # 添加面板到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, 1)  # 中间面板占据更多空间
        main_layout.addWidget(right_panel)
        
        # 数据初始化
        self.images = []  # 存储PIL Image对象
        self.image_paths = []  # 存储文件路径
        self.current_image_index = -1
        self.watermark_position = 'top-left'  # 默认水印位置（使用位置标识符）
        self.templates = {}
        self.templates_dir = os.path.join(os.path.expanduser('~'), '.watermarker2', 'templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        self.loadTemplates()
        
    def importImages(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, '导入图片', '', '图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)'
        )
        self.addImages(files)
        
    def batchImportImages(self):
        directory = QFileDialog.getExistingDirectory(self, '选择文件夹', '')
        if directory:
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            files = [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f)) and 
                   any(f.lower().endswith(ext) for ext in supported_formats)
            ]
            self.addImages(files)
    
    def addImages(self, files):
        for file_path in files:
            if file_path not in self.image_paths:
                try:
                    image = Image.open(file_path)
                    self.images.append(image)
                    self.image_paths.append(file_path)
                    
                    # 添加到列表显示
                    item = QListWidgetItem(os.path.basename(file_path))
                    
                    # 创建缩略图用于显示
                    thumbnail = image.copy()
                    thumbnail.thumbnail((150, 100))
                    # 将PIL图像手动转换为QImage
                    width, height = thumbnail.size
                    if thumbnail.mode == 'RGB':
                        bytes_per_line = 3 * width
                        qimage = QImage(thumbnail.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    elif thumbnail.mode == 'RGBA':
                        bytes_per_line = 4 * width
                        qimage = QImage(thumbnail.tobytes(), width, height, bytes_per_line, QImage.Format_RGBA8888)
                    else:
                        # 转换为RGB
                        rgb_thumbnail = thumbnail.convert('RGB')
                        bytes_per_line = 3 * width
                        qimage = QImage(rgb_thumbnail.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    # 正确的做法：将QPixmap转换为QIcon
                    item.setIcon(QIcon(QPixmap.fromImage(qimage)))
                    
                    self.image_list.addItem(item)
                except Exception as e:
                    QMessageBox.warning(self, '错误', f'无法打开文件 {file_path}: {str(e)}')
        
        # 如果是第一次导入图片，自动选择第一张
        if self.image_list.count() > 0 and self.current_image_index == -1:
            self.image_list.setCurrentRow(0)
            self.onImageSelected(self.image_list.item(0))
    
    def onImageSelected(self, item):
        index = self.image_list.row(item)
        if 0 <= index < len(self.images):
            self.current_image_index = index
            self.updatePreview()
    
    def dragEnterEvent(self, event):
        # 检查拖入的是否为文件
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        # 允许在窗口中移动拖拽的文件
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        # 处理拖放的文件
        if event.mimeData().hasUrls():
            # 获取拖入的文件路径列表
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            # 过滤出图片文件
            image_files = []
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            for file_path in files:
                # 如果是目录，递归获取所有图片文件
                if os.path.isdir(file_path):
                    for root, dirs, files_in_dir in os.walk(file_path):
                        for f in files_in_dir:
                            if any(f.lower().endswith(ext) for ext in supported_formats):
                                image_files.append(os.path.join(root, f))
                # 如果是文件，检查是否为支持的图片格式
                elif any(file_path.lower().endswith(ext) for ext in supported_formats):
                    image_files.append(file_path)
            # 添加图片如果是QPoint对象（通过鼠标拖拽设置），根据预览窗口与实际图片的比例进行缩放
            if image_files:
                self.addImages(image_files)
    
    def onMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.watermark_position = event.pos()
            self.updatePreview()

    def onMouseMove(self, event):
        if self.dragging:
            self.watermark_position = event.pos()
            self.updatePreview()

    def onMouseRelease(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            
    def updatePreview(self):
        if self.current_image_index == -1 or not self.images:
            return
        
        # 获取当前图片
        image = self.images[self.current_image_index].copy()
        
        # 如果没有水印文本，直接显示原图
        watermark_text = self.text_content.toPlainText().strip()
        if not watermark_text:
            self.displayImage(image)
            return
        
        # 创建绘制对象
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # 设置字体
        try:
            # 获取粗体和斜体状态
            bold = self.bold_check.isChecked()
            italic = self.italic_check.isChecked()
            
            # 根据粗体和斜体选择合适的字体文件
            font = None
            
            # 尝试加载适合当前样式的字体
            if bold:
                # 优先尝试加载粗体字体
                try:
                    font = ImageFont.truetype('msyhbd.ttc', self.font_size.value())
                except:
                    try:
                        font = ImageFont.truetype('simhei.ttf', self.font_size.value())
                    except:
                        pass
            
            # 如果粗体字体加载失败，尝试其他字体
            if font is None:
                font_names = ['msyh.ttc', 'simhei.ttf', 'simsun.ttc']
                for font_name in font_names:
                    try:
                        font = ImageFont.truetype(font_name, self.font_size.value())
                        break
                    except (OSError, IOError):
                        continue
            
            # 如果找不到指定字体，使用默认字体
            if font is None:
                font = ImageFont.load_default()
        except Exception as e:
            # 字体设置出错时使用默认字体
            font = ImageFont.load_default()
        
        # 获取透明度值（确保使用正确的滑块值）
        opacity_value = int(self.opacity_slider.value() * 2.55)
        
        # 获取文本尺寸（Pillow 9.0+ 版本兼容方式）
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]  # right - left
        text_height = bbox[3] - bbox[1]  # bottom - top
        
        # 计算实际位置
        img_width, img_height = image.size
        
        # 处理位置逻辑
        if isinstance(self.watermark_position, str):
            # 如果是位置标识符（从预设按钮选择），根据图片大小计算实际位置
            pos_x, pos_y = self.calculateActualPosition(
                self.watermark_position, img_width, img_height, text_width, text_height
            )
        else:
            # 如果是QPoint对象（通过鼠标拖拽设置），根据预览窗口与实际图片的比例进行缩放
            preview_width = self.preview_label.size().width()
            preview_height = self.preview_label.size().height()
            
            # 计算图片在预览窗口中的实际显示尺寸（保持宽高比）
            img_ratio = img_width / img_height
            preview_ratio = preview_width / preview_height
            
            if img_ratio > preview_ratio:
                # 图片更宽，以宽度为准
                scaled_width = preview_width
                scaled_height = int(preview_width / img_ratio)
            else:
                # 图片更高，以高度为准
                scaled_height = preview_height
                scaled_width = int(preview_height * img_ratio)
            
            # 计算图片在预览窗口中的偏移量（居中显示）
            offset_x = (preview_width - scaled_width) // 2
            offset_y = (preview_height - scaled_height) // 2
            
            # 获取鼠标点击位置
            click_x = self.watermark_position.x()
            click_y = self.watermark_position.y()
            
            # 检查点击是否在图片区域内
            if offset_x <= click_x < offset_x + scaled_width and offset_y <= click_y < offset_y + scaled_height:
                # 将点击位置转换为相对于图片的位置
                relative_x = click_x - offset_x
                relative_y = click_y - offset_y
                
                # 计算缩放比例并转换到实际图片坐标
                scale_x = img_width / scaled_width
                scale_y = img_height / scaled_height
                pos_x = int(relative_x * scale_x)
                pos_y = int(relative_y * scale_y)
            else:
                # 如果点击在图片区域外，默认居中显示
                pos_x, pos_y = self.calculateActualPosition('center', img_width, img_height, text_width, text_height)
        
        # 保存原始位置信息，用于旋转时的位置计算
        original_position = self.watermark_position
        
        # 应用旋转
        if self.rotate_slider.value() != 0:
            # 创建一个新的透明图像用于旋转水印
            temp_img = Image.new('RGBA', (text_width * 2, text_height * 2), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # 在临时图像中央绘制文本
            temp_draw.text(
                (text_width, text_height),
                watermark_text,
                font=font,
                fill=self.getColorWithOpacity(),
                anchor='mm'
            )
            
            # 如果需要斜体效果，先应用斜体变换
            if italic:
                # 应用剪切变换来创建斜体效果
                shear_factor = 0.25
                width, height = temp_img.size
                
                # 创建变换矩阵，添加水平偏移补偿
                transform = (1, shear_factor, -height * shear_factor / 2, 0, 1, 0)
                
                # 计算新的宽度（考虑剪切后的扩展）
                new_width = int(width + height * abs(shear_factor))
                
                # 应用变换
                temp_img = temp_img.transform(
                    (new_width, height),
                    Image.AFFINE,
                    transform,
                    Image.BICUBIC
                )
                
                # 更新文本宽度以适应斜体变换
                text_width = new_width
            
            # 旋转临时图像
            rotated_img = temp_img.rotate(self.rotate_slider.value(), expand=1)
            
            # 计算旋转后图像的尺寸
            rot_width, rot_height = rotated_img.size
            
            # 对于预设位置（如左下、右下等），确保旋转后的文本仍然保持在相应位置
            if isinstance(original_position, str):
                # 重新计算旋转后的位置，确保它保持在选定的区域内
                if original_position == 'top-left':
                    pos_x = 10
                    pos_y = 10
                elif original_position == 'top-right':
                    pos_x = img_width - rot_width - 10
                    pos_y = 10
                elif original_position == 'bottom-left':
                    pos_x = 10
                    pos_y = img_height - rot_height - 10
                elif original_position == 'bottom-right':
                    pos_x = img_width - rot_width - 10
                    pos_y = img_height - rot_height - 10
                elif original_position == 'center':
                    pos_x = (img_width - rot_width) // 2
                    pos_y = (img_height - rot_height) // 2
            else:
                # 对于鼠标拖拽的位置，使用原有的计算方式
                pos_x = max(0, min(pos_x - rot_width // 2, img_width - rot_width))
                pos_y = max(0, min(pos_y - rot_height // 2, img_height - rot_height))
            
            # 粘贴旋转后的水印到原图
            image.paste(rotated_img, (pos_x, pos_y), rotated_img)
        else:
            # 直接在原图上绘制文本，添加边界检查以确保文本不会超出图片范围
            # 为了确保透明度正确应用，统一使用临时图像方式绘制
            
            # 创建临时图像
            temp_img = Image.new('RGBA', (text_width * 2, text_height * 2), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # 在临时图像中央绘制文本
            temp_draw.text(
                (text_width // 2, text_height // 2),
                watermark_text,
                font=font,
                fill=self.getColorWithOpacity()
            )
            
            # 如果需要斜体效果，应用变换
            if italic:
                shear_factor = 0.25
                width, height = temp_img.size
                
                # 创建变换矩阵（不添加偏移）
                transform = (1, shear_factor, 0, 0, 1, 0)
                
                # 计算新的宽度（考虑剪切后的扩展）
                new_width = int(width + height * abs(shear_factor))
                
                # 应用变换
                temp_img = temp_img.transform(
                    (new_width, height),
                    Image.AFFINE,
                    transform,
                    Image.BICUBIC
                )
            
            # 调整位置，确保文本完全在图片范围内
            paste_x = max(0, min(pos_x - text_width // 2, img_width - temp_img.width))
            paste_y = max(0, min(pos_y - text_height // 2, img_height - temp_img.height))
            
            # 粘贴到原图，使用临时图像作为mask确保透明度正确
            image.paste(temp_img, (paste_x, paste_y), temp_img)
        # 显示处理后的图像
        self.displayImage(image)
    
    def displayImage(self, image):
        # 将PIL图像转换为QImage
        # 将PIL图像手动转换为QImage
        width, height = image.size
        if image.mode == 'RGB':
            bytes_per_line = 3 * width
            qimage = QImage(image.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
        elif image.mode == 'RGBA':
            bytes_per_line = 4 * width
            qimage = QImage(image.tobytes(), width, height, bytes_per_line, QImage.Format_RGBA8888)
        else:
            # 转换为RGB
            rgb_image = image.convert('RGB')
            bytes_per_line = 3 * width
            qimage = QImage(rgb_image.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
        
        # 确保图像在预览窗口中完全显示，同时保持宽高比
        pixmap = QPixmap.fromImage(qimage)
        
        # 获取预览标签的可用大小（考虑边框等）
        available_size = self.preview_label.size()
        
        # 计算缩放比例，确保图片完全显示在预览窗口中
        scaled_pixmap = pixmap.scaled(
            available_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # 创建一个新的QPixmap作为画布，大小与预览标签相同
        display_pixmap = QPixmap(available_size)
        display_pixmap.fill(Qt.transparent)  # 填充透明背景
        
        # 在画布中央绘制缩放后的图像
        painter = QPainter(display_pixmap)
        x = (available_size.width() - scaled_pixmap.width()) // 2
        y = (available_size.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
        
        # 显示图像
        self.preview_label.setPixmap(display_pixmap)
        
        # 重新设置鼠标追踪以启用拖拽功能
        self.preview_label.setMouseTracking(True)
        self.preview_label.mousePressEvent = self.onMousePress
        self.preview_label.mouseMoveEvent = self.onMouseMove
        self.dragging = False
    
    def onMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.watermark_position = event.pos()
            self.updatePreview()
    
    def onMouseMove(self, event):
        if self.dragging:
            self.watermark_position = event.pos()
            self.updatePreview()
    
    def setWatermarkPosition(self, position):
        # 如果传入的是字符串标识符（位置预设按钮调用），保存标识符而非实际坐标
        # 如果传入的是QPoint（鼠标拖拽调用），保存实际坐标
        self.watermark_position = position
        self.updatePreview()
    
    def calculateActualPosition(self, position_identifier, image_width, image_height, text_width, text_height):
        # 根据位置标识符计算实际位置
        margin = 30  # 增加安全边距
        if position_identifier == 'top-left':
            return (margin, margin)
        elif position_identifier == 'top-right':
            return (image_width - text_width - margin, margin)
        elif position_identifier == 'bottom-left':
            return (margin, image_height - text_height - margin)
        elif position_identifier == 'bottom-right':
            return (image_width - text_width - margin, image_height - text_height - margin)
        elif position_identifier == 'center':
            return ((image_width - text_width) // 2, (image_height - text_height) // 2)
        else:
            return (position_identifier.x(), position_identifier.y())
    
    def selectColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.font_color = color.name()
            self.color_button.setStyleSheet(f'background-color: {self.font_color}; color: white;')
            self.updatePreview()
    
    def getColorWithOpacity(self):
        # 解析颜色
        color = QColor(self.font_color)
        r, g, b = color.red(), color.green(), color.blue()
        opacity = int(self.opacity_slider.value() * 2.55)  # 转换为0-255范围
        return (r, g, b, opacity)
    
    def togglePrefixSuffix(self):
        if self.name_combo.currentIndex() in [1, 2]:  # 添加前缀或添加后缀
            self.prefix_suffix_layout.itemAt(0).widget().show()
            self.prefix_suffix_input.show()
        else:
            self.prefix_suffix_layout.itemAt(0).widget().hide()
            self.prefix_suffix_input.hide()
    
    def toggleQualitySlider(self, format):
        if format == 'JPEG':
            self.quality_slider.setEnabled(True)
        else:
            self.quality_slider.setEnabled(False)
    
    def exportImage(self):
        if self.current_image_index == -1 or not self.images:
            QMessageBox.warning(self, '警告', '请先选择一张图片')
            return
        
        # 获取保存路径
        original_path = self.image_paths[self.current_image_index]
        original_name = os.path.basename(original_path)
        original_dir = os.path.dirname(original_path)
        
        # 根据命名规则生成新文件名
        new_name = original_name
        if self.name_combo.currentIndex() == 1:  # 添加前缀
            prefix = self.prefix_suffix_input.text() or 'wm_'
            new_name = f'{prefix}{original_name}'
        elif self.name_combo.currentIndex() == 2:  # 添加后缀
            suffix = self.prefix_suffix_input.text() or '_watermarked'
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f'{name_parts[0]}{suffix}.{name_parts[1]}'
            else:
                new_name = f'{name_parts[0]}{suffix}'
        
        # 根据输出格式调整扩展名
        format = self.format_combo.currentText().lower()
        name_parts = new_name.rsplit('.', 1)
        if len(name_parts) == 2:
            new_name = f'{name_parts[0]}.{format}'
        else:
            new_name = f'{name_parts[0]}.{format}'
        
        # 显示保存对话框，不允许保存到原文件夹
        save_path, _ = QFileDialog.getSaveFileName(
            self, '导出图片', os.path.join(os.path.expanduser('~'), new_name),
            f'{format.upper()} 文件 (*.{format})'
        )
        
        if save_path:
            # 检查是否保存到原文件夹
            if os.path.dirname(save_path) == original_dir:
                reply = QMessageBox.question(
                    self, '确认', '您正在保存到原图片所在文件夹，可能会覆盖原文件。是否继续？',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            try:
                # 获取处理后的图像
                image = self.images[self.current_image_index].copy()
                
                # 应用水印
                watermark_text = self.text_content.toPlainText().strip()
                if watermark_text:
                    draw = ImageDraw.Draw(image, 'RGBA')
                    
                    try:
                        # 根据粗体斜体选择不同的字体文件
                        if self.bold_check.isChecked() and self.italic_check.isChecked():
                            font = ImageFont.truetype('arialbi.ttf', self.font_size.value())  # 粗斜体
                        elif self.bold_check.isChecked():
                            font = ImageFont.truetype('arialbd.ttf', self.font_size.value())  # 粗体
                        elif self.italic_check.isChecked():
                            font = ImageFont.truetype('ariali.ttf', self.font_size.value())   # 斜体
                        else:
                            font = ImageFont.truetype('arial.ttf', self.font_size.value())    # 常规
                    except:
                        # 如果找不到指定字体，使用默认字体
                        font = ImageFont.load_default()
                    
                    # 计算实际位置
                    img_width, img_height = image.size
                    
                    # 获取文本尺寸（Pillow 9.0+ 版本兼容方式）
                    bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = bbox[2] - bbox[0]  # right - left
                    text_height = bbox[3] - bbox[1]  # bottom - top
                    
                    # 处理位置逻辑
                    if isinstance(self.watermark_position, str):
                        # 如果是位置标识符，根据图片大小计算实际位置
                        pos_x, pos_y = self.calculateActualPosition(
                            self.watermark_position, img_width, img_height, text_width, text_height
                        )
                    else:
                        # 使用与updatePreview相同的坐标转换逻辑
                        preview_width = self.preview_label.size().width()
                        preview_height = self.preview_label.size().height()
                        
                        img_ratio = img_width / img_height
                        preview_ratio = preview_width / preview_height
                        
                        if img_ratio > preview_ratio:
                            scaled_width = preview_width
                            scaled_height = int(preview_width / img_ratio)
                        else:
                            scaled_height = preview_height
                            scaled_width = int(preview_height * img_ratio)
                        
                        offset_x = (preview_width - scaled_width) // 2
                        offset_y = (preview_height - scaled_height) // 2
                        
                        click_x = self.watermark_position.x()
                        click_y = self.watermark_position.y()
                        
                        if offset_x <= click_x < offset_x + scaled_width and offset_y <= click_y < offset_y + scaled_height:
                            relative_x = click_x - offset_x
                            relative_y = click_y - offset_y
                            scale_x = img_width / scaled_width
                            scale_y = img_height / scaled_height
                            pos_x = int(relative_x * scale_x)
                            pos_y = int(relative_y * scale_y)
                        else:
                            pos_x, pos_y = self.calculateActualPosition('center', img_width, img_height, text_width, text_height)
                    
                    if self.rotate_slider.value() != 0:
                        temp_img = Image.new('RGBA', (text_width * 2, text_height * 2), (255, 255, 255, 0))
                        temp_draw = ImageDraw.Draw(temp_img)
                        temp_draw.text(
                            (text_width, text_height),
                            watermark_text,
                            font=font,
                            fill=self.getColorWithOpacity(),
                            anchor='mm'
                        )
                        rotated_img = temp_img.rotate(self.rotate_slider.value(), expand=1)
                        rot_width, rot_height = rotated_img.size
                        
                        if isinstance(self.watermark_position, str):
                            if self.watermark_position == 'top-left':
                                pos_x, pos_y = 10, 10
                            elif self.watermark_position == 'top-right':
                                pos_x = img_width - rot_width - 10
                                pos_y = 10
                            elif self.watermark_position == 'bottom-left':
                                pos_x = 10
                                pos_y = img_height - rot_height - 10
                            elif self.watermark_position == 'bottom-right':
                                pos_x = img_width - rot_width - 10
                                pos_y = img_height - rot_height - 10
                            elif self.watermark_position == 'center':
                                pos_x = (img_width - rot_width) // 2
                                pos_y = (img_height - rot_height) // 2
                        else:
                            pos_x = max(0, min(pos_x - rot_width // 2, img_width - rot_width))
                            pos_y = max(0, min(pos_y - rot_height // 2, img_height - rot_height))
                        
                        image.paste(rotated_img, (pos_x, pos_y), rotated_img)
                    else:
                        # 对于未旋转的水印，如果使用预设位置，重新计算准确位置
                        if isinstance(self.watermark_position, str):
                            pos_x, pos_y = self.calculateActualPosition(
                                self.watermark_position, img_width, img_height, text_width, text_height
                            )
                        
                        # 确保文本完全在图片范围内
                        pos_x = max(0, min(pos_x, img_width - text_width))
                        pos_y = max(0, min(pos_y, img_height - text_height))
                        
                        draw.text(
                            (pos_x, pos_y),
                            watermark_text,
                            font=font,
                            fill=self.getColorWithOpacity()
                        )
                
                # 保存图像
                if format == 'jpeg':
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    image.save(save_path, quality=self.quality_slider.value())
                else:
                    image.save(save_path)
                
                QMessageBox.information(self, '成功', f'图片已保存至: {save_path}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'保存图片时出错: {str(e)}')
    
    def batchProcess(self):
        if not self.images:
            QMessageBox.warning(self, '警告', '请先导入图片')
            return
        
        # 选择输出文件夹
        output_dir = QFileDialog.getExistingDirectory(self, '选择输出文件夹', os.path.expanduser('~'))
        if not output_dir:
            return
        
        # 处理每张图片
        for i, (image, path) in enumerate(zip(self.images, self.image_paths)):
            try:
                # 复制图像
                processed_image = image.copy()
                
                # 应用水印
                watermark_text = self.text_content.toPlainText().strip()
                if watermark_text:
                    draw = ImageDraw.Draw(processed_image, 'RGBA')
                    
                    try:
                        font_style = ''
                        if self.bold_check.isChecked():
                            font_style += 'bold'
                        if self.italic_check.isChecked():
                            if font_style:
                                font_style += 'italic'
                            else:
                                font_style += 'italic'
                        
                        font = ImageFont.truetype('arial.ttf', self.font_size.value())
                    except:
                        font = ImageFont.load_default()
                    
                    # 计算实际位置（使用默认位置或上次设置的位置）
                    img_width, img_height = processed_image.size
                    
                    # 获取文本尺寸（Pillow 9.0+ 版本兼容方式）
                    bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = bbox[2] - bbox[0]  # right - left
                    text_height = bbox[3] - bbox[1]  # bottom - top
                    
                    # 处理位置逻辑
                    if isinstance(self.watermark_position, str):
                        # 如果是位置标识符，根据图片大小计算实际位置
                        pos_x, pos_y = self.calculateActualPosition(
                            self.watermark_position, img_width, img_height, text_width, text_height
                        )
                    else:
                        # 使用与updatePreview相同的坐标转换逻辑
                        preview_width = self.preview_label.size().width()
                        preview_height = self.preview_label.size().height()
                        
                        img_ratio = img_width / img_height
                        preview_ratio = preview_width / preview_height
                        
                        if img_ratio > preview_ratio:
                            scaled_width = preview_width
                            scaled_height = int(preview_width / img_ratio)
                        else:
                            scaled_height = preview_height
                            scaled_width = int(preview_height * img_ratio)
                        
                        offset_x = (preview_width - scaled_width) // 2
                        offset_y = (preview_height - scaled_height) // 2
                        
                        click_x = self.watermark_position.x()
                        click_y = self.watermark_position.y()
                        
                        if offset_x <= click_x < offset_x + scaled_width and offset_y <= click_y < offset_y + scaled_height:
                            relative_x = click_x - offset_x
                            relative_y = click_y - offset_y
                            scale_x = img_width / scaled_width
                            scale_y = img_height / scaled_height
                            pos_x = int(relative_x * scale_x)
                            pos_y = int(relative_y * scale_y)
                        else:
                            pos_x, pos_y = self.calculateActualPosition('center', img_width, img_height, text_width, text_height)
                    
                    if self.rotate_slider.value() != 0:
                        temp_img = Image.new('RGBA', (text_width * 2, text_height * 2), (255, 255, 255, 0))
                        temp_draw = ImageDraw.Draw(temp_img)
                        temp_draw.text(
                            (text_width, text_height),
                            watermark_text,
                            font=font,
                            fill=self.getColorWithOpacity(),
                            anchor='mm'
                        )
                        rotated_img = temp_img.rotate(self.rotate_slider.value(), expand=1)
                        rot_width, rot_height = rotated_img.size
                        
                        if isinstance(self.watermark_position, str):
                            if self.watermark_position == 'top-left':
                                pos_x, pos_y = 10, 10
                            elif self.watermark_position == 'top-right':
                                pos_x = img_width - rot_width - 10
                                pos_y = 10
                            elif self.watermark_position == 'bottom-left':
                                pos_x = 10
                                pos_y = img_height - rot_height - 10
                            elif self.watermark_position == 'bottom-right':
                                pos_x = img_width - rot_width - 10
                                pos_y = img_height - rot_height - 10
                            elif self.watermark_position == 'center':
                                pos_x = (img_width - rot_width) // 2
                                pos_y = (img_height - rot_height) // 2
                        else:
                            pos_x = max(0, min(pos_x - rot_width // 2, img_width - rot_width))
                            pos_y = max(0, min(pos_y - rot_height // 2, img_height - rot_height))
                        
                        processed_image.paste(rotated_img, (pos_x, pos_y), rotated_img)
                    else:
                        # 对于未旋转的水印，如果使用预设位置，重新计算准确位置
                        if isinstance(self.watermark_position, str):
                            pos_x, pos_y = self.calculateActualPosition(
                                self.watermark_position, img_width, img_height, text_width, text_height
                            )
                        
                        # 确保文本完全在图片范围内
                        pos_x = max(0, min(pos_x, img_width - text_width))
                        pos_y = max(0, min(pos_y, img_height - text_height))
                        
                        draw.text(
                            (pos_x, pos_y),
                            watermark_text,
                            font=font,
                            fill=self.getColorWithOpacity()
                        )
                
                # 生成输出文件名
                original_name = os.path.basename(path)
                
                # 根据命名规则生成新文件名
                new_name = original_name
                if self.name_combo.currentIndex() == 1:  # 添加前缀
                    prefix = self.prefix_suffix_input.text() or 'wm_'
                    new_name = f'{prefix}{original_name}'
                elif self.name_combo.currentIndex() == 2:  # 添加后缀
                    suffix = self.prefix_suffix_input.text() or '_watermarked'
                    name_parts = original_name.rsplit('.', 1)
                    if len(name_parts) == 2:
                        new_name = f'{name_parts[0]}{suffix}.{name_parts[1]}'
                    else:
                        new_name = f'{name_parts[0]}{suffix}'
                
                # 根据输出格式调整扩展名
                format = self.format_combo.currentText().lower()
                name_parts = new_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f'{name_parts[0]}.{format}'
                else:
                    new_name = f'{name_parts[0]}.{format}'
                
                # 保存图像
                save_path = os.path.join(output_dir, new_name)
                if format == 'jpeg':
                    if processed_image.mode == 'RGBA':
                        processed_image = processed_image.convert('RGB')
                    processed_image.save(save_path, quality=self.quality_slider.value())
                else:
                    processed_image.save(save_path)
                
            except Exception as e:
                QMessageBox.warning(self, '错误', f'处理图片 {path} 时出错: {str(e)}')
                continue
        
        QMessageBox.information(self, '完成', f'批量处理已完成，共处理 {len(self.images)} 张图片')
    
    def saveTemplate(self):
        template_name, ok = QInputDialog.getText(self, '保存模板', '请输入模板名称:')
        if ok and template_name.strip():
            # 收集当前设置
            template = {
                'text': self.text_content.toPlainText(),
                'font_size': self.font_size.value(),
                'font_color': self.font_color,
                'opacity': self.opacity_slider.value(),
                'bold': self.bold_check.isChecked(),
                'italic': self.italic_check.isChecked(),
                'rotation': self.rotate_slider.value(),
                'position': {
                    'x': self.watermark_position.x(),
                    'y': self.watermark_position.y()
                },
                'output_format': self.format_combo.currentIndex(),
                'naming_rule': self.name_combo.currentIndex(),
                'prefix_suffix': self.prefix_suffix_input.text(),
                'quality': self.quality_slider.value()
            }
            
            # 保存模板到文件
            template_path = os.path.join(self.templates_dir, f'{template_name}.json')
            try:
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                
                # 更新模板列表
                self.loadTemplates()
                QMessageBox.information(self, '成功', f'模板 "{template_name}" 已保存')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'保存模板时出错: {str(e)}')
    
    def loadTemplate(self):
        selected_item = self.template_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, '警告', '请先选择一个模板')
            return
        
        template_name = selected_item.text()
        template_path = os.path.join(self.templates_dir, f'{template_name}.json')
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # 应用模板设置
            self.text_content.setPlainText(template.get('text', ''))
            self.font_size.setValue(template.get('font_size', 32))
            self.font_color = template.get('font_color', '#000000')
            self.color_button.setStyleSheet(f'background-color: {self.font_color}; color: white;')
            self.opacity_slider.setValue(template.get('opacity', 50))
            self.bold_check.setChecked(template.get('bold', False))
            self.italic_check.setChecked(template.get('italic', False))
            self.rotate_slider.setValue(template.get('rotation', 0))
            
            position = template.get('position', {'x': 10, 'y': 10})
            self.watermark_position = QPoint(position['x'], position['y'])
            
            self.format_combo.setCurrentIndex(template.get('output_format', 0))
            self.name_combo.setCurrentIndex(template.get('naming_rule', 0))
            self.prefix_suffix_input.setText(template.get('prefix_suffix', ''))
            self.quality_slider.setValue(template.get('quality', 90))
            
            # 更新预览
            self.updatePreview()
            QMessageBox.information(self, '成功', f'模板 "{template_name}" 已加载')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载模板时出错: {str(e)}')
    
    def deleteTemplate(self):
        selected_item = self.template_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, '警告', '请先选择一个模板')
            return
        
        template_name = selected_item.text()
        reply = QMessageBox.question(
            self, '确认', f'确定要删除模板 "{template_name}" 吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            template_path = os.path.join(self.templates_dir, f'{template_name}.json')
            try:
                os.remove(template_path)
                self.loadTemplates()
                QMessageBox.information(self, '成功', f'模板 "{template_name}" 已删除')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'删除模板时出错: {str(e)}')
    
    def loadTemplates(self):
        self.template_list.clear()
        
        try:
            # 获取模板文件夹中的所有.json文件
            template_files = [
                f for f in os.listdir(self.templates_dir)
                if f.endswith('.json')
            ]
            
            # 添加到模板列表
            for template_file in template_files:
                template_name = template_file[:-5]  # 移除.json后缀
                self.template_list.addItem(template_name)
        except Exception as e:
            print(f'加载模板时出错: {str(e)}')
    
    def loadSettings(self):
        # 加载上次关闭时的设置
        settings_dir = os.path.join(os.path.expanduser('~'), '.watermarker2')
        settings_file = os.path.join(settings_dir, 'settings.json')
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 应用设置
                if 'last_template' in settings and settings['last_template']:
                    # 查找并加载上次使用的模板
                    for i in range(self.template_list.count()):
                        if self.template_list.item(i).text() == settings['last_template']:
                            self.template_list.setCurrentRow(i)
                            self.loadTemplate()
                            break
        except Exception as e:
            print(f'加载设置时出错: {str(e)}')
    
    def saveSettings(self):
        # 保存当前设置
        settings_dir = os.path.join(os.path.expanduser('~'), '.watermarker2')
        os.makedirs(settings_dir, exist_ok=True)
        settings_file = os.path.join(settings_dir, 'settings.json')
        
        try:
            settings = {
                'last_template': self.template_list.currentItem().text() if self.template_list.currentItem() else ''
            }
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'保存设置时出错: {str(e)}')
    
    def closeEvent(self, event):
        # 保存设置并关闭应用
        self.saveSettings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WatermarkerApp()
    window.show()
    sys.exit(app.exec_())
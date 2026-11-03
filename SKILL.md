---
name: ibi-emoji
description: 根据文字或动作参考图，为蓝白脑部吉祥物创作表情包、透明贴纸和角色变体。复用随包提供的脑部、电路与复旦校徽固定母版，支持已有22款素材的再组合和新表情前景生成。适用于这个角色的连续创作。
---

# 脑智角色表情创作

## 角色规则

`assets/body/master.svg` 是身体的唯一母版。脑轮廓、电路线和校徽作为一个整体变换。校徽在母版内的相对坐标为 `(0.72, 0.68)`，直径占母版宽度的 `0.267`。每款配置只描述身体整体姿态和前景层。

校徽随身体一起缩放、旋转。手套、表情、书本、爱心、被子等前景可以自然遮住它。保持原稿中的 `FUDAN UNIVERSITY` 和 `1905`，文字随固定母版嵌入。母版校验值保存在 `assets/body/geometry.json`。

角色采用圆润脑形、蓝白两半、深蓝轮廓、白手套和蓝白运动鞋。母版中的白色区域保持不透明，画布背景使用真实 Alpha 透明。

用户明确要求重新设计身体时，另存母版版本并记录新的校验值，再让整组变体引用同一新版本。

## 开始创作

1. 查看 `assets/body/master.png` 和 `assets/gallery.png`。从 `assets/catalog.json` 找一到两款接近所需动作的实例。只读取实际需要的实例和前景。
2. 根据用户要求确定情绪、眼神、手势、道具及文案。参考图片用于判断这些要素。用户没有指定文案时，默认制作无字透明底，并在交付时说明。
3. 已有动作可以复用 `assets/foreground/NN.png`。新动作使用当前环境的内置图像编辑工具生成独立前景层，调用前查看角色参考和用户提供的参考图。读取 [前景生成提示词](references/foreground-prompts.md) 并替换动作与布局。
4. 把新前景保存到用户的工作目录，创建该作品自己的场景 JSON。读取 [合成参数](references/composition.md)，用 `scripts/render.py` 合成固定身体与前景。
5. 查看输出 PNG 在浅色底上的实际效果，检查眼神、指尖方向、手指数量、肢体连接、遮挡、画面裁切和文字。必要时修正前景或身体整体姿态，再重新合成。

若当前环境没有图像生成能力，可以用随包的素材进行组合，并明确说明新动作前景仍需图像工具或人工绘制。

## 工具与交付

所有脚本按自身位置寻找素材，可从任意工作目录调用。首次运行的依赖安装见仓库 `README.md`。

```bash
python /path/to/ibi-emoji/scripts/render.py --example 22 --output ./outputs/gesture
python /path/to/ibi-emoji/scripts/render.py --config ./work/scene.json --output ./outputs/new-emoji
python /path/to/ibi-emoji/scripts/verify.py --output ./outputs/new-emoji
```

默认导出透明 PNG、自包含的分层 SVG、浅色背景预览和制作记录。保留实际使用的生成提示词、前景原文件及场景 JSON。给用户展示预览，并链接透明 PNG。说明所采用的默认文案选择和任何仍未修好的可见问题。

`verify.py` 检查身体母版、图层和输出的一致性。视觉验收仍需逐张进行，尤其关注手部与道具的遮挡关系。

当用户明确需要印刷交付时，读取 [印刷交接](references/printing.md)，确认实际尺寸后增加排版和刀线文件。

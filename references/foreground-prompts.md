# 前景生成

将母版和最接近的完整角色图交给内置图像编辑工具作为角色参考。用户图片提供动作和情绪参考。先查看图片，再调用工具。

前景层包含眼睛、眉毛、嘴、腮红、手套、手臂、腿、鞋及道具。脑部身体会在合成时加入。向工具明确请求真实透明背景，并要求原画布上的空间布局。

替换下面提示词中的花括号内容，并根据生成结果调整描述。

```text
Use case: compositing.
Character reference: the attached blue-white brain cartoon mascot.
Pose reference: the user's reference image, when present.
Create a foreground layer for this mascot performing {action} with {emotion and gaze}.
Keep the rounded 2D sticker style, dark navy outlines, white gloves, blue arms and legs, blue-white sneakers.
Hand gesture details: {which fingers extend, their directions, hand orientation and overlap}.
Output only floating facial features, arms, gloves, legs, shoes and requested props on genuine alpha transparency.
Leave the entire brain body area empty, including its silhouette, circuitry and red seal. The exact existing body master will be composited behind this layer.
Canvas and layout: {aspect ratio}; the absent body occupies {normalized box}; eyes near {positions}; hands near {positions}; feet near {positions}.
Keep disconnected components at those positions. Preserve opaque white gloves and props. Retain only the requested caption or prop lettering, spelled exactly {text or none}.
Crisp edges with antialiasing. Empty areas have zero alpha. Keep soft shadows confined within objects.
```

身体被移除后的前景看起来会是分散的五官和肢体。合成后再判断最终角色效果。工具可能改变画布尺寸，因此场景参数使用实际输出的尺寸和归一化坐标。

若生成了完整身体，继续编辑该结果以分离前景。若保留了旧电路线或校徽碎片，修复前景后再合成。针对缺陷做一次局部修正，再查看输出。

附带的 22 款前景和场景配置可直接用作布局参考。其中 09 展示睡觉时的遮挡，14 展示腿部在身体后面，22 展示上下相对的双指手势。

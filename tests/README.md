# v05 回归检查

在仓库根目录，用 Python 3.10+ 运行：

```text
python -B -m unittest discover -s tests -p "test_*.py" -v
```

只使用 Python 标准库，不要求安装 Blender。Token 测试使用临时合成日志；进度测试使用合成事件及不含用户路径的代表日志行。不会读取私人会话、调用模型或写入作品目录。

这些测试检查用量边界和进度状态逻辑。它们不能证明 Blender 在目标设备上的渲染性能或视觉质量；真实小图执行与当前未覆盖范围见 [验证记录](../docs/usage-progress.md#验证记录)。

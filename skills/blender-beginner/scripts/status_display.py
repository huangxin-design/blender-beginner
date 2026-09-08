"""Write a local render/usage HTML snapshot; no server or background monitor."""
import argparse
from datetime import datetime, timezone
import html
import json
import math
import os
from pathlib import Path
import tempfile


PHASES = {
    "initializing": "正在准备", "waiting_for_frame": "等待帧进度", "preparing_frame": "准备当前帧",
    "sampling": "正在采样", "rendering_or_saving": "正在渲染或保存",
    "frame_outputs_complete": "计划帧已输出，等待执行结束", "process_completed": "本次执行结束",
    "failed": "执行失败", "timeout": "已到时间上限", "interrupted": "执行已中断",
}
STATES = {"starting": "准备中", "running": "进行中", "completed": "本次执行结束",
          "failed": "执行失败", "timeout": "已到时间上限", "interrupted": "执行已中断"}
BASES = {
    "no_verified_plan": "尚无核实过的帧计划", "collecting_complete_frames": "正在积累完整帧耗时",
    "empirical_recent_frames_low_confidence": "根据近期完整帧估算，可信度较低",
    "current_frame_exceeded_observed_range": "当前帧已超出观测范围，等待新依据",
    "stale_progress": "等待新的 Blender 进度", "frame_outputs_complete": "计划帧已输出",
    "terminal": "执行已停止，剩余时间不再估计",
}
TOKEN_STATES = {"observed_pending": "持续记录 · 尚待结算", "close_requested_pending": "已请求收尾 · 等待尾部记录",
                "closed_observed": "已收尾 · 覆盖范围有限", "closed_partial": "已截停 · 记录不完整"}


def esc(value):
    if value is None:
        return "待记录"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return html.escape(str(value), quote=True)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def duration(value):
    if not number(value):
        return "待记录"
    seconds = math.ceil(value)
    if seconds < 60:
        return f"{seconds} 秒"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} 小时 {minutes} 分 {seconds} 秒" if hours else f"{minutes} 分 {seconds} 秒"


def count(value):
    return f"{int(value):,}" if number(value) and value == int(value) else "待记录"


def frame_number(value):
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else "待记录"


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            local = parsed.astimezone()
            offset = local.strftime("%z")
            return esc(local.strftime("%Y-%m-%d %H:%M:%S") + f" UTC{offset[:3]}:{offset[3:]}")
    except ValueError:
        pass
    return esc(value)


def coverage_text(value):
    if not isinstance(value, dict):
        return esc(value)
    events = count(value.get("usage_events_since_baseline"))
    missing = count(value.get("missing_usage_events"))
    return f"本次关联会话的已观察区间；用量记录 {events} 条，缺失用量 {missing} 条。项目归属未自动证明，子代理未计入。"


def write_display(status: dict, output: Path, usage: dict | None = None) -> None:
    """Atomically replace the page. The caller owns periodic updates and process state."""
    state = status.get("status")
    active = state in ("starting", "running")
    snapshot = bool(status.get("display_snapshot"))
    updated = status.get("updated_at")
    try:
        stamp = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
    except (TypeError, ValueError):
        age = float("inf")
    stale = active and (age > 15 or age < -15)
    elapsed, progressed = status.get("elapsed_seconds"), status.get("progress_updated_elapsed")
    waiting = active and number(elapsed) and number(progressed) and elapsed - progressed > 15
    progress_age = f"{duration(elapsed - progressed)}前（截至页面更新时间）" if number(elapsed) and number(progressed) and progressed <= elapsed else "尚未收到"
    show_eta = active and not stale and not waiting
    sample_eta = duration(status.get("sample_eta_seconds")) if show_eta else "待记录"
    bounds = status.get("eta_range_seconds")
    valid_range = isinstance(bounds, (list, tuple)) and len(bounds) == 2 and all(number(v) for v in bounds) and bounds[0] <= bounds[1]
    eta = f"{duration(bounds[0])} — {duration(bounds[1])}" if show_eta and valid_range else "待记录"
    note = "状态已停止更新，预计剩余时间已隐藏；刷新页面可重新读取" if stale else "等待新的 Blender 进度" if waiting else "按最新记录显示，不独立倒数"
    phase = status.get("phase")
    phase_text = STATES.get(state, "状态待记录") if not active else PHASES.get(phase, phase or "待记录")
    refresh = '<meta id="refresh" http-equiv="refresh" content="2">' if active and not stale and not snapshot else ""
    token_panel = ""
    if usage is not None:
        data = usage.get("usage") or {}
        metrics = (("输入", "input_tokens"), ("其中：缓存输入", "cached_input_tokens"),
                   ("输出", "output_tokens"), ("其中：推理输出", "reasoning_output_tokens"))
        cells = "".join(f"<div><span>{label}</span><strong>{count(data.get(key))}</strong></div>" for label, key in metrics)
        token_panel = f'''<section class="panel"><div class="eyebrow">项目已记录 TOKEN</div>
<h2>{esc(usage.get('project_id'))} <small>{esc(TOKEN_STATES.get(usage.get('status'), usage.get('status')))}</small></h2>
<p class="total">{count(data.get('total_tokens'))}<span> token</span></p><div class="tokens">{cells}</div>
<p class="hint">缓存输入包含在输入中；推理输出包含在输出中，不额外累加。</p>
<p class="hint">记录截至：{timestamp(usage.get('observed_through'))}<br>覆盖范围：{coverage_text(usage.get('coverage'))}</p>
<p class="hint">{esc(usage.get('notes'))}</p></section>'''
    mode = "静态快照 · 重新生成后查看新记录" if snapshot else "执行器持续写入时，每 2 秒刷新页面" if active else "执行结束记录"
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{refresh}<title>Blender · 本次进度</title>
<style>
:root{{color-scheme:light;font-family:"Microsoft YaHei","PingFang SC",sans-serif;color:#234037;background:#f6f3eb}}
*{{box-sizing:border-box}}body{{margin:0;padding:48px 24px}}main{{max-width:1000px;margin:auto}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:2px;color:#657b6d}}header{{margin-bottom:28px}}
h1{{font-size:38px;letter-spacing:-1px;margin:12px 0}}h2{{font-size:25px;margin:14px 0 20px}}
.hint,footer{{font-size:13px;line-height:1.85;color:#687369;overflow-wrap:anywhere}}.panel{{background:#fffdf7;border:1px solid #dbe0d5;border-radius:22px;padding:28px;margin-bottom:20px}}
.badge{{display:inline-block;padding:7px 12px;border-radius:30px;background:#e5eee2;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:24px}}.metric{{background:#f0f1e7;border-radius:15px;padding:20px}}
.metric span,.tokens span{{display:block;font-size:12px;color:#687369;line-height:1.6}}strong{{display:block;font-size:24px;line-height:1.6;margin-top:8px}}
.wide{{grid-column:span 2}}.total{{font-size:40px;font-weight:700;margin:12px 0}}.total span{{font-size:15px;font-weight:400}}
.tokens{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}.tokens strong{{font-size:20px}}small{{font-size:12px;font-weight:400;color:#687369}}
#health{{padding:10px 14px;border-left:3px solid #8eaa87;background:#f2f3ec}}@media(max-width:650px){{body{{padding:28px 16px}}h1{{font-size:30px}}.grid,.tokens{{grid-template-columns:1fr 1fr}}.wide{{grid-column:span 2}}.panel{{padding:22px}}strong{{font-size:20px}}}}
</style></head><body><main data-updated="{esc(updated)}" data-active="{str(active).lower()}" data-snapshot="{str(snapshot).lower()}">
<header><div class="eyebrow">BLENDER 开工助手</div><h1>看清进度，再等下一帧。</h1><p class="hint">{mode}</p></header>
<section class="panel"><span class="badge">{esc(STATES.get(state, '状态待记录'))}</span><h2>{esc(phase_text)}</h2>
<div class="grid"><div class="metric"><span>已用时间</span><strong>{duration(elapsed)}</strong></div>
<div class="metric"><span>当前帧采样预计剩余</span><strong class="eta">{sample_eta}</strong></div>
<div class="metric"><span>成功输出帧 / 计划帧</span><strong>{count(status.get('completed_frames'))} / {count(status.get('total_frames'))}</strong></div>
<div class="metric wide"><span>整段帧输出预计剩余范围</span><strong class="eta">{eta}</strong></div>
<div class="metric"><span>当前帧 · 采样</span><strong>{frame_number(status.get('current_frame'))}</strong><span>{count(status.get('sample'))} / {count(status.get('samples_total'))}</span></div></div>
<p class="hint" id="health" role="status">{note}</p><p class="hint">估计依据：{esc(BASES.get(status.get('eta_basis'), status.get('eta_basis')))}<br>
页面更新时间：{timestamp(updated)}<br>最近渲染进度：{progress_age}<br>{esc(status.get('message') or '')}</p>
<p class="hint">剩余 0 秒只表示当前采样估计归零。范围仅覆盖本次计划帧输出，不含另行编码或验收。<br>执行结束不代表作品验收通过；输出完整性、画面及视频播放效果仍需另行检查。</p></section>
{token_panel}<footer>本页面只显示本次执行记录。原始日志与用量资料应保存在本地，不随作品默认公开。</footer>
</main><script>
const root=document.querySelector('main');
function checkFreshness(){{
 if(root.dataset.active!=='true'||root.dataset.snapshot==='true')return;
 const stamp=Date.parse(root.dataset.updated),age=Date.now()-stamp;
 if(!Number.isFinite(stamp)||age>15000||age< -15000){{
  document.querySelectorAll('.eta').forEach(el=>el.textContent='待记录');
  document.getElementById('health').textContent='状态已停止更新，预计剩余时间已隐藏；刷新页面可重新读取';
  document.getElementById('refresh')?.remove();
 }}
}}
checkFreshness();setInterval(checkFreshness,1000);
</script></body></html>'''
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, suffix=".html", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(document)
        os.replace(temporary, output)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--usage", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {path.resolve() for path in (args.render, args.usage) if path}:
        parser.error("--output must not overwrite an input report.")
    status = json.loads(args.render.read_text(encoding="utf-8-sig"))
    usage = json.loads(args.usage.read_text(encoding="utf-8-sig")) if args.usage else None
    status["display_snapshot"] = True
    write_display(status, args.output, usage)
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()

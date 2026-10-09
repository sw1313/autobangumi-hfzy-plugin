"""4.0 插件入口。功能仍在 backend/hfzy，配置表单写回 config/hfzy.json。"""

import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ab_sdk import Plugin

_POLICY_TO_STORE = {"挂起": "hold", "替换": "replace", "hold": "hold", "replace": "replace"}


class HfzyOptions(BaseModel):
    player_enable: bool = Field(True, title="下载列表播放按钮")
    downloader_filter: bool = Field(
        True,
        title="下载列表筛选",
        description="在下载器标题右侧按进度筛选。未完成是进度不是 100% 的视频。",
    )
    downloader_eta_single_line: bool = Field(
        True,
        title="ETA 保持一行",
        description="下载列表的剩余时间写在一行里，不再因为时长把这一行撑高。",
    )
    rss_name_priority: bool = Field(True, title="RSS 优先使用填入名称")
    rss_episode_count: bool = Field(
        True,
        title="季度后显示过滤后的版本和视频",
        description="按当前过滤规则统计剩下的发布版本和视频条数，用来检查规则是否漏了或者全部挡住。",
    )
    rss_copy_fix: bool = Field(
        True,
        title="修复 RSS 复制按钮",
        description="用 http 打开页面时，RSS 源旁边的复制图标也能复制完整链接。",
    )
    rss_filter_hit: bool = Field(
        True,
        title="标记命中的过滤规则",
        description="某条过滤正则命中了 RSS 标题时，用橘黄色框标出这个标签。",
    )
    tmdb_include_adult: bool = Field(
        True,
        title="打开 TMDB 成人条目",
        description="搜索剧集和电影时包含 TMDB 标记为成人的动画。关闭后这些条目不会出现在搜索结果里。",
    )
    tmdb_info: bool = Field(
        True,
        title="添加时填写 TMDB 编号",
        description="解析器是 TMDB 且没有打开聚合 RSS 时，可以选剧集或电影并填入编号。",
    )
    rss_form_season: bool = Field(
        True,
        title="添加时以填写的季度为准",
        description="收集和订阅时，对话框里的季度优先于文件名上的季号。",
    )
    rss_advanced_complete: bool = Field(
        True,
        title="补齐添加时的高级设置",
        description="添加 RSS 的高级设置补上编辑规则里已有的季度偏移、放送星期、内容类型、偏好字幕组和偏好分辨率。",
    )
    special_rename: bool = Field(
        True,
        title="特别篇按第 0 季重命名",
        description="订阅内容类型是特别篇时，TVSP、OVA、SP、特别篇这类文件改成 S00E 编号。剧场版不依赖这个开关。",
    )
    revision_group_fallback: bool = Field(
        True,
        title="识别方括号里的更高修订版",
        description="标题里的 [v2] 会当成修订 2。发布组名字带空格时，用开头的方括号补上。",
    )
    revision_single_video: bool = Field(
        True,
        title="字幕压缩包不算第二集",
        description="判断能不能自动替换时只数视频。字幕或字体压缩包不再把这一集算成多文件。",
    )
    revision_conflict_policy: Literal["挂起", "替换"] = Field(
        "挂起",
        title="修订冲突",
        description="同一集已经有文件时，更高修订版怎么处理。挂起保留旧文件；替换会用新修订版换掉旧文件。",
    )


class HfzyPlugin(Plugin[HfzyOptions]):
    config_model = HfzyOptions

    async def setup(self) -> None:
        backend = str(Path(__file__).resolve().parent / "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        from hfzy.bootstrap import _install_page_script, install
        from hfzy.config import attach_hfzy_settings, save_hfzy_dict
        from module.conf import settings

        install()
        _install_page_script()
        data = self.config.model_dump()
        data["revision_conflict_policy"] = _POLICY_TO_STORE.get(
            data["revision_conflict_policy"], "hold"
        )
        save_hfzy_dict(data)
        attach_hfzy_settings(settings)

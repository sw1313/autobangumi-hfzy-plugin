import type { HfzyMisc } from './types';

export const hfzyApi = {
  async getConfig() {
    const { data } = await axios.get<HfzyMisc>('api/v1/extensions/hfzy/config', {
      silent: true,
    });
    return data;
  },
  async updateConfig(payload: HfzyMisc) {
    const { data } = await axios.patch<{ msg_en: string; msg_zh: string }>(
      'api/v1/extensions/hfzy/config',
      payload
    );
    return data;
  },
  async rssEpisodeCount(payload: {
    rss_link: string;
    filter: string[];
    season: number;
    episode_type: string;
  }) {
    const { data } = await axios.post<{
      versions: number;
      videos: number;
      hits?: string[];
    }>(
      'api/v1/extensions/hfzy/rss-episode-count',
      payload,
      { silent: true }
    );
    return data;
  },
};

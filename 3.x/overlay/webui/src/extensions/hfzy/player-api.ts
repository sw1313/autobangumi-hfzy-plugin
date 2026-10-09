export interface PlayerMediaFile {
  name: string;
  path: string;
  url: string;
  size: number;
}

export const playerApi = {
  async resolveTorrent(hash: string) {
    const { data } = await axios.get<{
      files: PlayerMediaFile[];
      msg_en?: string;
      msg_zh?: string;
    }>(`api/v1/extensions/player/torrents/${hash}/media`, { silent: true });
    return data;
  },
};

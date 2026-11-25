# Quiet TV 航拍素材

Quiet TV 的航拍屏保通过 [在线目录](https://beatsad.github.io/quiet-tv-aerial/catalog.signed.json) 获取素材。每段视频和预览图有独立的固定地址，电视在下载后核对文件大小及 SHA-256。

| 素材 | 来源 |
| --- | --- |
| 内华达山脉 | [Sierra Buttes North](https://www.dvidshub.net/video/1025362/sierra-buttes-north)，Andrew Avitt / USDA Forest Service |
| 夏威夷福特岛 | [Aerial video of Ford Island](https://www.dvidshub.net/video/901074/aerial-video-ford-island)，Sgt. Kyler Chatman / U.S. Army / Commander Navy Region Hawaii |

DVIDS 将这两段原片标为公有领域。原片及预览图使用遵循 [DVIDS 使用说明](https://www.dvidshub.net/about/copyright)。

The appearance of U.S. Department of War (DoW) visual information does not imply or constitute DoW endorsement.

## 添加素材

1. 使用新的 `aerial-<id>`，把 H.264 MP4 放入 `docs/media/`，并将 720 × 405 PNG 放入 `docs/posters/`。单段 MP4 最大 100 MiB。
2. 在 `catalog.json` 追加记录，填入文件大小、SHA-256、尺寸、时长、帧率及出处，递增 `revision`。已发布的 ID、素材和预览图保持原样。
3. 使用 Python 3 和 OpenSSL 在本地签名，私钥保存在仓库之外。

   ```sh
   python3 sign_catalog.py --key /path/to/aerial-signing.pem
   ```

4. 提交素材、目录与签名文件到 `main`。GitHub Pages 发布 `docs/`，电视会加载经过签名验证的新目录。

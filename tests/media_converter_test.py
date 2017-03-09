from unittest import TestCase, mock
from media_converter import MediaConverter, codecs
from media_converter.tracks import VideoTrack, AudioTrack
from media_converter.streams import VideoOutstream


class TestMediaConverter(TestCase):
    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_simple_convert(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.mkv'
        MediaConverter('a.mp4', 'b.mkv').convert()

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', 'a.mp4',
               '-map', '0:v:0', '-c:v', 'h264', '-crf', '23', '-pix_fmt', 'yuv420p',
               '-profile:v', 'high', '-level', '3.1',
               '-map', '0:a:0', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-ar', '44100',
               'tmp.mkv']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.mkv', 'b.mkv')

    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_audio_convert(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.m4a'
        MediaConverter(AudioTrack('a.wav', codecs.AAC('256k', 2, 44100)), 'a.m4a').convert()

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', 'a.wav',
               '-map', '0:a:0', '-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-ar', '44100',
               'tmp.m4a']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.m4a', 'a.m4a')

    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_video_convert(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.mkv'
        MediaConverter([VideoTrack('a.mp4', codecs.MPEG2('3000k', '16:9', '23.97')),
                        AudioTrack('a.mp4', codecs.MP2('256k', 2, 44100))], 'b.mkv').convert()

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', 'a.mp4',
               '-map', '0:v:0', '-c:v', 'mpeg2video', '-b:v', '3000k', '-aspect', '16:9', '-r', '23.97',
               '-map', '0:a:0', '-c:a', 'mp2', '-b:a', '256k', '-ac', '2', '-ar', '44100',
               'tmp.mkv']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.mkv', 'b.mkv')

    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_convert_to_480p(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.mkv'

        vos = VideoOutstream('a.mp4').scale(height=480)
        MediaConverter([VideoTrack(vos, codecs.MPEG2('3000k', '16:9', '23.97')),
                        AudioTrack('a.mp4', codecs.AAC('256k', 2, 44100))], 'b.mkv').convert()

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', 'a.mp4',
               '-filter_complex', '[0:v:0]scale=-2:480[vout0]',
               '-map', '[vout0]', '-c:v', 'mpeg2video', '-b:v', '3000k', '-aspect', '16:9', '-r', '23.97',
               '-map', '0:a:0', '-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-ar', '44100',
               'tmp.mkv']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.mkv', 'b.mkv')

    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_h265_with_ac3(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.mp4'

        MediaConverter([VideoTrack('a.mkv', codecs.H265(constant_rate_factor=18, preset='slow')),
                        AudioTrack('a.mkv', codecs.AC3('448k', 6, 48000))], 'b.mp4').convert()

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', 'a.mkv',
               '-map', '0:v:0', '-c:v', 'libx265', '-preset', 'slow', '-x265-params', 'crf=18',
               '-map', '0:a:0', '-c:a', 'ac3', '-b:a', '448k', '-ac', '6', '-ar', '48000',
               'tmp.mp4']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.mp4', 'b.mp4')

    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_silent_audio_for_10_secs(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.m4a'

        MediaConverter([AudioTrack(None, codecs.AAC('256k', 2, 48000))], 'b.m4a').convert(duration=10)

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-ar', '48000', '-ac', '1', '-f', 's16le', '-i', '/dev/zero',
               '-map', '0:a:0', '-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-ar', '48000', '-t', '10',
               'tmp.m4a']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.m4a', 'b.m4a')

    @mock.patch('shutil.move')
    @mock.patch('media_converter.MediaConverter._new_tmp_filepath')
    @mock.patch('subprocess.call')
    def test_blank_video_with_audio(self, mock_subprocess, mock_tmp_filepath, mock_shutil):
        mock_tmp_filepath.return_value = 'tmp.mp4'

        MediaConverter([VideoTrack(None, codecs.H264()),
                        AudioTrack('a.mp3', codecs.AAC())], 'b.mp4').convert()

        cmd = ['/usr/local/bin/ffmpeg', '-y',
               '-s', '640x360', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-r', '30', '-i', '/dev/zero',
               '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', 'a.mp3',
               '-map', '0:v:0', '-c:v', 'h264', '-crf', '23', '-pix_fmt', 'yuv420p',
               '-profile:v', 'high', '-level', '3.1',
               '-map', '1:a:0', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-ar', '44100',
               '-shortest',
               'tmp.mp4']
        mock_subprocess.assert_called_with(cmd)
        mock_shutil.assert_called_with('tmp.mp4', 'b.mp4')

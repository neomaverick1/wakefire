// The two switches players reach for on a phone: music (and the night ambience under it) and
// sounds (effects and voices). Kept in the device's preferences.
using UnityEngine;

namespace Wakefire
{
    public static class Settings
    {
        public static bool MusicOn = true, SoundOn = true;

        public static void Load()
        {
            MusicOn = PlayerPrefs.GetInt("wf_music", 1) == 1;
            SoundOn = PlayerPrefs.GetInt("wf_sound", 1) == 1;
            Apply();
        }

        public static void Apply()
        {
            Music.Volume = MusicOn ? 0.65f : 0f;
            Music.AmbVolume = MusicOn ? 0.5f : 0f;
            Sfx.Volume = SoundOn ? 0.9f : 0f;
            Voice.Volume = SoundOn ? 0.55f : 0f;
        }

        public static void Toggle(bool music)
        {
            if (music) MusicOn = !MusicOn; else SoundOn = !SoundOn;
            PlayerPrefs.SetInt("wf_music", MusicOn ? 1 : 0);
            PlayerPrefs.SetInt("wf_sound", SoundOn ? 1 : 0);
            PlayerPrefs.Save();
            Apply();
        }
    }
}

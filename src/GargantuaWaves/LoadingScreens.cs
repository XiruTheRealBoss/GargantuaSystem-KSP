using System.IO;
using System.Linq;
using UnityEngine;

namespace GargantuaSystem
{
    /// <summary>
    /// Adds the mod's in-game photos (PluginData/LoadingScreens/*.jpg) to KSP's loading screen rotation.
    /// Runs before the game database loads, so the images are read from disk, not from GameDatabase.
    /// </summary>
    [KSPAddon(KSPAddon.Startup.Instantly, true)]
    public class LoadingScreens : MonoBehaviour
    {
        void Awake()
        {
            string dir = Path.Combine(KSPUtil.ApplicationRootPath, "GameData/GargantuaSystem/PluginData/LoadingScreens");
            if (LoadingScreen.Instance == null || !Directory.Exists(dir)) return;
            Texture2D[] images = Directory.GetFiles(dir, "*.jpg").Select(f =>
            {
                var t = new Texture2D(2, 2, TextureFormat.RGB24, false);
                t.LoadImage(File.ReadAllBytes(f), true);
                return t;
            }).ToArray();
            // the first state is the splash/logo; the rest are the long "loading" rotations
            foreach (var state in LoadingScreen.Instance.Screens.Skip(1))
                state.screens = (state.screens ?? new Texture2D[0]).Concat(images).ToArray();
            Debug.Log("[GargantuaSystem] LoadingScreens: added " + images.Length + " images");
        }
    }
}

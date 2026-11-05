using System;
using UnityEngine;

namespace GargantuaSystem
{
    /// <summary>
    /// Miller's time dilation (film: 1 hour = 7 years, ~60000x). KSP has one clock for the whole universe, so time
    /// spent with the active vessel inside Miller's sphere of influence is stored as a debt of
    /// (elapsed x (factor - 1)) seconds and paid back by jumping the universal clock forward.
    /// The jump only happens in the Space Center or Tracking Station: there is no vessel physics there, so every
    /// vessel just moves along its orbit like during a normal time warp. Jumping mid-flight could break unpacked vessels.
    /// The factor is GargantuaSystemSettings/TimeDilation (0 or 1 turns it off). The debt is saved with the game.
    /// </summary>
    [KSPScenario(ScenarioCreationOptions.AddToAllGames, GameScenes.FLIGHT, GameScenes.SPACECENTER, GameScenes.TRACKSTATION)]
    public class TimeDilation : ScenarioModule
    {
        const string BodyName = "Miller";

        double debt;            // seconds the rest of the universe still has to age
        double lastUT = -1;

        public override void OnSave(ConfigNode node) => node.SetValue("debt", debt.ToString("R", System.Globalization.CultureInfo.InvariantCulture), true);

        public override void OnLoad(ConfigNode node)
        {
            double.TryParse(node.GetValue("debt"), System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out debt);
        }

        double factor;
        CelestialBody miller;

        void Start()
        {
            factor = ReadFactor();
            miller = FlightGlobals.GetBodyByName(BodyName);
            if (factor <= 1 || miller == null) { debt = 0; enabled = false; return; }

            var scene = HighLogic.LoadedScene;
            if (debt > 0 && (scene == GameScenes.SPACECENTER || scene == GameScenes.TRACKSTATION))
            {
                double ut = Planetarium.GetUniversalTime();
                Planetarium.SetUniversalTime(ut + debt);
                ScreenMessages.PostScreenMessage(KSP.Localization.Localizer.Format("#LOC_GargSys_TimeDilation",
                    KSPUtil.PrintDateDelta(debt, true, false)), 12f, ScreenMessageStyle.UPPER_CENTER);
                Debug.Log("[GargantuaSystem] TimeDilation: universe aged " + debt.ToString("F0") + " s");
                debt = 0;
            }
            lastUT = Planetarium.GetUniversalTime();
        }

        void FixedUpdate()
        {
            double ut = Planetarium.GetUniversalTime();
            Vessel v = FlightGlobals.ActiveVessel;
            if (HighLogic.LoadedScene == GameScenes.FLIGHT && v != null && v.mainBody == miller && lastUT >= 0 && ut > lastUT)
                debt += (ut - lastUT) * (factor - 1);
            lastUT = ut;
        }

        static double ReadFactor()
        {
            foreach (ConfigNode n in GameDatabase.Instance.GetConfigNodes("GargantuaSystemSettings"))
                if (double.TryParse(n.GetValue("TimeDilation"), System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out double f))
                    return f;
            return 0;
        }
    }
}

#include "../ViewportLayout.h"
#include <cassert>
#include <limits>

int main()
{
    for (const auto size : {GameCore::ViewportRect{0,0,1280,720}, {0,0,800,450},
        {0,0,2560,720}, {0,0,1280,400}, {0,0,720,1280}, {0,0,3840,2160}})
    {
        const auto layout = GameCore::ViewportLayout::Fit(size.Width, size.Height);
        assert(layout.Valid && layout.Scale <= 1.5);
        assert(layout.Width >= 1280 && layout.Height >= 720);
        assert(std::abs(layout.Width * layout.Scale - size.Width) < 1e-8);
        const auto panel = layout.Centered(900,110);
        assert(panel.X >= 0 && panel.Y >= 0);
        assert(panel.Contains(panel.X,panel.Y));
        assert(!panel.Contains(panel.X+panel.Width,panel.Y));
        assert(!panel.Contains(panel.X,panel.Y+panel.Height));
    }
    const double nan = std::numeric_limits<double>::quiet_NaN();
    for (double invalid : {0.0, -1.0, nan, std::numeric_limits<double>::infinity()})
    {
        assert(!GameCore::ViewportLayout::Fit(invalid,720).Valid);
        assert(!GameCore::ViewportLayout::Fit(1280,invalid).Valid);
        assert(!GameCore::ViewportLayout::Fit(1280,720,invalid).Valid);
        assert(!GameCore::ViewportLayout::Fit(1280,720,1280,720,invalid).Valid);
    }
}

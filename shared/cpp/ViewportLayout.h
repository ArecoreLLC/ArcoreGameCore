#pragma once
#include <algorithm>
#include <cmath>

namespace GameCore
{
struct ViewportRect
{
    double X, Y, Width, Height;
    bool Contains(double x, double y) const
    {
        return x >= X && y >= Y && x < X + Width && y < Y + Height;
    }
};

// Pixel viewport to logical UI units. Fit both axes; never crop to a minimum scale.
// Invalid/minimized viewports return an inert layout with finite coordinates.
struct ViewportLayout
{
    double Scale = 1.0;
    double Width = 0.0;
    double Height = 0.0;
    bool Valid = false;

    static ViewportLayout Fit(double width, double height,
        double referenceWidth = 1280.0, double referenceHeight = 720.0,
        double maximumScale = 1.5)
    {
        ViewportLayout result;
        if (!std::isfinite(width) || !std::isfinite(height) ||
            !std::isfinite(referenceWidth) || !std::isfinite(referenceHeight) ||
            !std::isfinite(maximumScale) || width <= 0 || height <= 0 ||
            referenceWidth <= 0 || referenceHeight <= 0 || maximumScale <= 0)
            return result;
        const double scale = std::min({width / referenceWidth, height / referenceHeight, maximumScale});
        if (!std::isfinite(scale) || scale <= 0 ||
            !std::isfinite(width / scale) || !std::isfinite(height / scale)) return result;
        result.Scale = scale;
        result.Width = width / scale;
        result.Height = height / scale;
        result.Valid = true;
        return result;
    }

    ViewportRect Centered(double width, double height) const
    {
        return {(Width - width) / 2.0, (Height - height) / 2.0, width, height};
    }
};
}

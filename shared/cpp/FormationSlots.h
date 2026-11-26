#pragma once
#include <algorithm>
#include <cmath>

namespace GameCore
{
struct FormationOffset { double X = 0; double Y = 0; };
// Center rows independently, including an incomplete last row. Caller owns
// assignment stability and world-space orientation. Invalid requests return origin.
inline FormationOffset CenteredFormation(unsigned index, unsigned count,
    unsigned columns, double spacing)
{
    if (!count || count > 4096 || index >= count || !columns ||
        !std::isfinite(spacing) || spacing <= 0 || spacing > 1.e6) return {};
    columns = std::min(columns, count);
    const unsigned row = index / columns;
    const unsigned rows = (count + columns - 1) / columns;
    const unsigned inRow = std::min(columns, count - row * columns);
    return {(double(index % columns) - (inRow - 1) * 0.5) * spacing,
            (double(row) - (rows - 1) * 0.5) * spacing};
}
}

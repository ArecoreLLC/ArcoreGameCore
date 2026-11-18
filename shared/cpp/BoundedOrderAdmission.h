#pragma once
#include <cstddef>

namespace GameCore
{
enum class OrderAdmission { Replace, Append, RejectFull };

// Decide before mutating current work or pending orders. Capacity counts pending
// orders only. Authority, payload validation and storage belong to the consumer.
constexpr OrderAdmission AdmitOrder(bool append, std::size_t pending, std::size_t capacity)
{
    return !append ? OrderAdmission::Replace
        : pending < capacity ? OrderAdmission::Append : OrderAdmission::RejectFull;
}
}

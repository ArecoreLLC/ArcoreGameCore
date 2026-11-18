#include "../BoundedOrderAdmission.h"
#include <limits>
using GameCore::AdmitOrder;
using GameCore::OrderAdmission;
static_assert(AdmitOrder(true, 0, 8) == OrderAdmission::Append);
static_assert(AdmitOrder(true, 7, 8) == OrderAdmission::Append);
static_assert(AdmitOrder(true, 8, 8) == OrderAdmission::RejectFull);
static_assert(AdmitOrder(true, 9, 8) == OrderAdmission::RejectFull);
static_assert(AdmitOrder(true, 0, 0) == OrderAdmission::RejectFull);
static_assert(AdmitOrder(false, 8, 8) == OrderAdmission::Replace);
static_assert(AdmitOrder(false, 0, 0) == OrderAdmission::Replace);
static_assert(AdmitOrder(true, std::numeric_limits<std::size_t>::max(), 8) == OrderAdmission::RejectFull);
int main() { return 0; }

#define __SET_START_VALUES__ { \
r(input0_) = 0; \
r(input1_) = 1; \
r(input2_) = 2; \
r(input3_) = 3; \
r(input4_) = 4; \
r(input5_) = 5; \
}

#define __ARRAY_ELEMENTS__ \
comp->r[input0_], \
comp->r[input1_], \
comp->r[input2_], \
comp->r[input3_], \
comp->r[input4_], \
comp->r[input5_],

#define __CASE_LABELS__ \
case input0_: return r(input0_); \
case input1_: return r(input1_); \
case input2_: return r(input2_); \
case input3_: return r(input3_); \
case input4_: return r(input4_); \
case input5_: return r(input5_);

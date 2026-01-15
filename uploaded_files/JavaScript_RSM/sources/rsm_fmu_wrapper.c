#include <stdlib.h>
#define FMI_COSIMULATION
#include "rsm.h"

#include "generated/constants.h"

#define NUMBER_OF_REALS  (RSM_INPUTS + 1)
#define NUMBER_OF_INTEGERS 1
#define NUMBER_OF_BOOLEANS 0
#define NUMBER_OF_STRINGS 0
#define NUMBER_OF_STATES 1
#define NUMBER_OF_EVENT_INDICATORS 0

#include "fmuTemplate.h"

#define t_ 0
#define STATES { t_ }

#define rsm_output_ 0

#include "generated/snippets.h"

void setStartValues(ModelInstance *comp) {
  i(t_)      = 0;
  r(rsm_output_) = 0;
  __SET_START_VALUES__    
}

void initialize(ModelInstance* comp, fmiEventInfo* eventInfo) {
  eventInfo->upcomingTimeEvent   = fmiTrue;
  eventInfo->nextEventTime       = 1 + comp->time;
}

double rsm_evaluation_wrapper(ModelInstance *comp) {

  double arguments[] = {
    __ARRAY_ELEMENTS__
    0
  };

    initialization();

  return evaluate(arguments);
}

fmiReal getReal(ModelInstance* comp, fmiValueReference vr){
  switch(vr) {
    __CASE_LABELS__
    case rsm_output_: return rsm_evaluation_wrapper(comp);
    default: return 0;
  }
}

void updateEvent(ModelInstance *comp, fmiEventInfo *eventInfo) {
    eventInfo->upcomingTimeEvent   = fmiTrue;
    eventInfo->nextEventTime = 1 + comp->time;
}

void eventUpdate(ModelInstance *comp, fmiEventInfo *eventInfo) {
  r(rsm_output_) = rsm_evaluation_wrapper(comp);    
  i(t_) = i(t_) + 1;

  updateEvent(comp, eventInfo);
}

#include "fmuTemplate.c"

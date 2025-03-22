#ifndef CONFIG_H
#define CONFIG_H

// Define boolean settings
#define ENABLE_DEBUG false
#define PRETEND_FALSE false
#define USE_STEPPER_MOTOR true
#define SAFETY_CHECKS_ENABLED false
#define INVERT_DIRECTION false

#define STEPPER_PIPET_MICROSTEPS_CONFIG 8 //microsteps
#define LEAD_CONFIG 1 // mm/rev
#define VOLUME_TO_TRAVEL_RATIO_CONFIG 20 // ul/mm

#endif // CONFIG_H
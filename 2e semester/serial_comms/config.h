#ifndef CONFIG_H
#define CONFIG_H

// Define boolean settings
#define ENABLE_DEBUG false
#define PRETEND_FALSE false
#define USE_STEPPER_MOTOR false
#define SAFETY_CHECKS_ENABLED false
#define INVERT_DIRECTION false

#define STEPPER_PIPET_MICROSTEPS_CONFIG 16 //microsteps
#define LEAD_CONFIG 1 // mm/rev
#define VOLUME_TO_TRAVEL_RATIO_CONFIG 100 // ul/mm

#endif // CONFIG_H
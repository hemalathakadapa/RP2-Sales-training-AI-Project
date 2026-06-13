# Conversation stages

GREETING = "greeting"
WAITING_FOR_RP2 = "waiting_for_rp2"
WAITING_FOR_COURSE = "waiting_for_course"
COURSE_DISCUSSION = "course_discussion"
PROJECT_DISCUSSION = "project_discussion"
PLACEMENT_DISCUSSION = "placement_discussion"
CLOSING = "closing"
FINISHED = "finished"

# Maximum salesperson messages before AI starts closing
MAX_CHAT_LIMIT = 15


def get_next_stage(current_stage):
    """
    Returns the next logical conversation stage.
    """

    flow = {
        GREETING: WAITING_FOR_RP2,
        WAITING_FOR_RP2: WAITING_FOR_COURSE,
        WAITING_FOR_COURSE: COURSE_DISCUSSION,
        COURSE_DISCUSSION: PROJECT_DISCUSSION,
        PROJECT_DISCUSSION: PLACEMENT_DISCUSSION,
        PLACEMENT_DISCUSSION: CLOSING,
        CLOSING: FINISHED
    }

    return flow.get(current_stage, FINISHED)


def should_start_closing(chat_count):
    """
    Decide when the AI should begin closing the admission.
    """

    return chat_count >= MAX_CHAT_LIMIT
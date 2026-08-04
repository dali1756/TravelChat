import type { Activity } from './types'

export interface ActivityFormValues {
  title: string
  attraction_id: number | null
  start_time: string
  end_time: string
  note: string
}

export const EMPTY_ACTIVITY_FORM: ActivityFormValues = {
  title: '',
  attraction_id: null,
  start_time: '',
  end_time: '',
  note: '',
}

export function toFormValues(activity: Activity | null): ActivityFormValues {
  if (!activity) return EMPTY_ACTIVITY_FORM
  return {
    title: activity.title,
    attraction_id: activity.attraction?.id ?? null,
    start_time: activity.start_time ?? '',
    end_time: activity.end_time ?? '',
    note: activity.note,
  }
}

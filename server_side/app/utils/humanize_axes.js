// contains a mapping from JSON-formatted keys to humanized quantity names

export const simple_humanized_axes = {
  time_since: 'Time (relative)',
  time_of_day: 'Time of Day',

  temp_ref: 'Temp. (reference)',
  temp_sample: 'Temp. (sample)',

  heat_ref: 'Heat Flow (reference)',
  heat_sample: 'Heat Flow (sample)',
  heat_diff: 'Heat Difference'
};


const humanized_axes = {
  time_since: 'Time Since Start (s)',
  time_of_day: 'Time of Day',

  temp_ref: 'Reference Cell Temperature (°C)',
  temp_sample: 'Sample Cell Temperature (°C)',

  heat_ref: 'Reference Cell Heat Flow (mW)',
  heat_sample: 'Sample Cell Heat Flow (mW)',
  heat_diff: 'Heat Differential (mW)'
};

export default humanized_axes;
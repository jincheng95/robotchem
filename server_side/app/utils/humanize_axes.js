// contains a mapping from JSON-formatted keys to humanized quantity names

export const simple_humanized_axes = {
  time_since: 'Time (relative)',
  time_of_day: 'Time of Day',

  temp_ref: 'Temp. (reference)',
  temp_sample: 'Temp. (sample)',

  heat_ref: 'Heat (reference)',
  heat_sample: 'Heat (sample)',
  heat_diff: 'Heat Difference'
};


const humanized_axes = {
  time_since: 'Time Since Start (s)',
  time_of_day: 'Time of Day',

  temp_ref: 'Reference Cell Temperature (°C)',
  temp_sample: 'Sample Cell Temperature (°C)',

  heat_ref: 'Heat Supplied To Reference Cell (J)',
  heat_sample: 'Heat Supplied to Sample (J)',
  heat_diff: 'Heat Differential [Sample – Reference] (J)'
};

export default humanized_axes;
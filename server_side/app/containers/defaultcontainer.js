import React from 'react';

import Run from '../components/run/run';
import Start from '../components/start';

export default function DefaultContainer(props) {
  const {calorimeter} = props;

  if(!!calorimeter.has_active_runs) {
    return (
      <Run {...props} run={calorimeter.has_active_runs} expanded/>
    )
  } else {
    return (
      <Start {...props} />
    )
  }

}
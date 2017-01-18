import React from 'react';

import RefreshIndicator from 'material-ui/RefreshIndicator';

export default function Refreshing(props) {

  const {size, message, zDepth} = props;

  return (
    <div style={{position: 'relative', height: `${size * 1.5}px`, margin: '1em 0'}}>
      <RefreshIndicator
        size={size}
        left={-Math.round(size/2)}
        top={28}
        zDepth={(!!zDepth || zDepth == 0) ? zDepth : 1}
        status={'loading'}
        style={{marginLeft: '50%'}}
      />
      <p className="text-muted text-center">
        {message}
      </p>
    </div>
  )
}
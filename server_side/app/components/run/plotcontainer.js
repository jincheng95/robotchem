import React, {Component} from 'react';
import moment from 'moment';
import includes from 'lodash/includes';
import concat from 'lodash/concat';

import LinePlot from './lineplot';
import {ReferenceLine} from 'recharts';

export default class PlotContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      plots: [
        {
          type: 'line',
          xKey: 'time_since',
          yKeys: ['temp_ref', 'temp_sample',]
        },
      ]
    };
    this.getReferenceLines = this.getReferenceLines.bind(this);
    this.renderIndividualPlot = this.renderIndividualPlot.bind(this);
  }

  getReferenceLines(xKey, yKeys) {
    const {run, data_points} = this.props;
    const {start_temp, target_temp, is_finished} = run;

    var refs = [];
    if( includes(yKeys, 'temp_ref') || includes(yKeys, 'temp_sample') ){
      refs = concat(refs, [
        (<ReferenceLine key="start-temp" y={start_temp} label="Start Temperature" stroke="red" strokeDasharray="5 5"/>),
        (<ReferenceLine key="target-temp" y={target_temp} label="End Temperature" stroke="red" strokeDasharray="5 5"/>),
      ]);
    }

    if ( xKey == 'time_since' && !is_finished ) {
      const diff = moment().diff(data_points[0].measured_at, 'seconds');
      refs = concat(refs,
        (<ReferenceLine key="now-relative" x={diff} label="Now" stroke="grey" strokeDasharray="3 3"/>)
      );
    }
    return refs;
  }

  renderIndividualPlot(type, index, extraProps) {
    var plot;
    switch (type) {
      case "line":
        plot = LinePlot;
        break;
      default:
        plot = LinePlot;
    }

    const props = {
      data: this.props.data_points,
      key: index,
      ...extraProps,
    };
    return <plot {...props}/>;
  }

  render() {
    const { plots } = this.state;
    return (
      <div>
        <h4>{plots.length > 1 ? "PLOTS" : "PLOT"}</h4>
          {plots.map((value, index) => {
            return this.renderIndividualPlot(
              value.type,
              index,
              {referenceLines: this.getReferenceLines(value.xKey, value.yKeys), ...value}
            ).bind(this);
          })}
      </div>
    )
  }
}
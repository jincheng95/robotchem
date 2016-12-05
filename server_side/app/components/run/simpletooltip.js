import React, {Component} from 'react';
import findKey from 'lodash/findKey';
import includes from 'lodash/includes';

import Paper from 'material-ui/Paper';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';

import TwoColumnRow from '../TwoColumnRow';
import {simple_humanized_axes} from '../../utils/humanize_axes';
import units from '../../utils/units';

const ToolTipLabel = (props) => (
  <div>
    <span className="text-muted" style={{marginRight: '5px', fontWeight: props.bold ? '800': null}}>
      {props.title}
    </span>
    <span className="pull-right" style={{fontWeight: props.bold ? '800': null, textAlign: 'right'}}>
      {props.value}
    </span>
  </div>
);

export default class SimpleTooltip extends Component {
  render() {
    const {active} = this.props;

    if (active) {
      const {payload, label, xLabel} = this.props;
      const humanizedXLabel = simple_humanized_axes[xLabel];
      const xUnit = units[xLabel];

      return (
        <MuiThemeProvider>
          <Paper zDepth={5} style={{maxWidth: '300px', padding: '0.5em', opacity: '0.75'}}>
            <ToolTipLabel title={humanizedXLabel} value={`${label} ${xUnit}`} bold/>

            <hr style={{margin: '0.3em 0.1em 0.3em 0.2em'}}/>

            {payload.map((payload, index) => {
              const yLabel = payload.dataKey;
              const humanizedYLabel = simple_humanized_axes[yLabel];
              const yUnit = units[yLabel];
              return (
                <ToolTipLabel key={index} title={humanizedYLabel} value={`${payload.value} ${yUnit}`}/>
              )
            })}
          </Paper>
        </MuiThemeProvider>
      )
    }

    return null;
  }
}

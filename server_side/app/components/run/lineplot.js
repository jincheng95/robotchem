import React, {Component} from 'react';

import {XAxis, YAxis, CartesianGrid, Line, LineChart, Tooltip, Legend, ResponsiveContainer} from 'recharts';
import SimpleTooltip from './simpletooltip';
import list_of_colors from '../../utils/list_of_colors';
import humanized_axes from '../../utils/humanize_axes';


export default class LinePlot extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { data, yKeys, xKey, referenceLines } = this.props;

    return(
      <ResponsiveContainer minHeight={300}>
        <LineChart data={data} height={300} width={500} minHeight={250}>
          <XAxis dataKey={xKey} label={humanized_axes[xKey]}
                 type="number" allowDecimals={false}
                 padding={{right: 3}}/>
          <YAxis domain={['auto', 'auto']}
                 allowDecimals={false}
                 type="number" />

          <CartesianGrid />

          <Tooltip content={<SimpleTooltip xLabel={xKey}/>}/>
          <Legend />

          {referenceLines}

          {yKeys.map((value, index) => {
            return (
              <Line key={index} type="monotone" dataKey={value} name={humanized_axes[value]}
                    stroke={list_of_colors[index]} />
            )
          })}
        </LineChart>
      </ResponsiveContainer>
    )
  }
}
import React, {Component} from 'react';

import {XAxis, YAxis, CartesianGrid, Line, LineChart, Tooltip, Legend, ResponsiveContainer, Brush} from 'recharts';
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
      <ResponsiveContainer minHeight={350}>
          <LineChart data={data} minHeight={350} syncId="1"
                     margin={{top: 20, right: 40, left: -5, bottom: 2}}>

            <XAxis dataKey={xKey} label={humanized_axes[xKey]}
                   domain={['auto', 'auto']} tickCount={12}
                   type="number"/>
            <YAxis domain={['auto', 'auto']} tickCount={6}
                   type="number" />

            <CartesianGrid />
            <Tooltip content={<SimpleTooltip xLabel={xKey}/>}/>
            <Legend />

            {referenceLines}

            {yKeys.map((value, index) => {
              return (
                <Line key={index} type="monotone" dataKey={value} name={humanized_axes[value]}
                      isAnimationActive={false}
                      stroke={list_of_colors[index]} />
              )
            })}


          </LineChart>
      </ResponsiveContainer>
    )
  }
}
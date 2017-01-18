import React from "react";
import moment from "moment";
import {XAxis, YAxis, CartesianGrid, Line, LineChart, Tooltip, Legend, ResponsiveContainer, Brush} from "recharts";
import SimpleTooltip from "./simpletooltip";
import list_of_colors from "../../utils/list_of_colors";
import humanized_axes from "../../utils/humanize_axes";
import units from "../../utils/units";
import clamp from 'lodash/clamp';


export default class LinePlot extends React.PureComponent {
  constructor(props) {
    super(props);
  }

  render() {
    const { data, yKeys, xKey, referenceLines, is_active } = this.props;
    const xTickFormatter = xKey == 'time_of_day' ? (datetime) => moment(datetime, 'X').format('H:mm:ss') : null;

    return(
      <ResponsiveContainer minHeight={350}>
          <LineChart data={data} minHeight={350} syncId="1"
                     margin={{top: 20, right: 40, left: -5, bottom: 2}}>

            <XAxis dataKey={xKey} label={humanized_axes[xKey]}
                   domain={['dataMin', 'dataMax']} tickCount={12} units={units[xKey]}
                   type="number"
                   tickFormatter={xTickFormatter}/>
            <YAxis domain={['dataMin', 'auto']} tickCount={6}
                   type="number"/>

            <CartesianGrid />
            <Tooltip content={<SimpleTooltip xLabel={xKey}/>}/>
            <Legend />

            {referenceLines}

            {yKeys.map((value, index) => {
              return (
                <Line key={index} type="monotone" dataKey={value} name={humanized_axes[value]}
                      isAnimationActive={false}
                      strokeWidth={3}
                      stroke={list_of_colors[index]} />
              )
            })}

            {(!is_active) && <Brush height={40} width={15} dataKey={xKey} data={data}
                                    travellerWidth={25} tickFormatter={xTickFormatter}/>}

          </LineChart>
      </ResponsiveContainer>
    )
  }
}
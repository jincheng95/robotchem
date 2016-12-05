import React from 'react';

import {TableRow, TableRowColumn} from 'material-ui/Table';

const TwoColumnRow = (props) => {
  return (
    <TableRow>
      <TableRowColumn><strong>{props.title}</strong></TableRowColumn>
      <TableRowColumn>{props.value}</TableRowColumn>
    </TableRow>
  )
};

export default TwoColumnRow;
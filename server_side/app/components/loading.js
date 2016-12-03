import React from 'react';
import Snackbar from 'material-ui/Snackbar';

const LoadingSnackBar = (props) => {
  return (
    <Snackbar message="Loading..." open={props.open}/>
  );
};

export default LoadingSnackBar;
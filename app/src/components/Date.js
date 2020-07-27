import React, { Component } from 'react';

import { Typography } from '@material-ui/core';

import { timestampToMonthYear } from '../utils'


export default class Date extends Component {
    constructor(props) {
        super(props);
        this.date = timestampToMonthYear(this.props.time)
    }

    render() {

        const {
            date = timestampToMonthYear(this.props.time)
        } = this.props;

        return (
            <div className="panel" id="date">
                <Typography color="textSecondary">
                    {date.month}
                </Typography>
                <Typography variant="h6" color="textPrimary">
                    {date.year}
                </Typography>
            </div>
        );
    }
}
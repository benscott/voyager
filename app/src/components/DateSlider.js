import React, { Component } from 'react';
import 'mapbox-gl/dist/mapbox-gl.css';

// Material UI
import 'fontsource-roboto';
import { PlayArrow, Pause, Replay } from '@material-ui/icons';
import { IconButton, Typography, Slider } from '@material-ui/core';
import Grid from '@material-ui/core/Grid';


// https://material-ui.com/api/slider/

export default class DatePanel extends Component {

    constructor(props) {
        super(props);
        this.onPlayClick = this.onPlayClick.bind(this)
        this.onResetClick = this.onResetClick.bind(this)
        this.onSliderMouseDown = this.onSliderMouseDown.bind(this)
        this.onSliderMouseUp = this.onSliderMouseUp.bind(this)
        this.onSliderChange = this.onSliderChange.bind(this)
        this.animatedState = false
    }

    onPlayClick() {
        this.props.timeToggle()
    }

    onResetClick() {
        this.props.timeReset()
    }

    onSliderMouseDown() {
        this.animatedState = this.props.isAnimated
        this.props.timeStop()
    }

    onSliderMouseUp() {
        // We only restart time, if the animation was actually playing
        if (this.animatedState) {
            this.props.timeStart();
        }
    }

    onSliderChange(event, value) {
        this.props.timeUpdate(value);
    }

    render() {
        const {
            sliderMax = this.props.linearScaleRange,
            sliderStep = 10,
            // date = this._formatTimeToDate(this.props.time)
        } = this.props;

        return (
            <div id="date-slider">

                <div className="panel">

                    <Grid container spacing={3}>

                        <Grid item xs={2} align="center">
                            <IconButton aria-label="Restart" color="primary" onClick={this.onResetClick}>
                                <Replay />
                            </IconButton>

                            <IconButton aria-label="play" color="primary" onClick={this.onPlayClick}>
                                {this.props.isAnimated ? (
                                    <Pause />
                                ) : (
                                        <PlayArrow />
                                    )}

                            </IconButton>
                        </Grid>

                        <Grid item xs={2} align="right">
                            <Typography color="textSecondary">
                                {this.props.scaleLabels.min}
                            </Typography>
                        </Grid>

                        <Grid item xs={6} align="center">

                            <Slider
                                value={this.props.time}
                                min={0}
                                step={sliderStep}
                                max={sliderMax}
                                // valueLabelDisplay="auto"
                                aria-labelledby="date"
                                onChange={this.onSliderChange}
                                onMouseDown={this.onSliderMouseDown}
                                onMouseUp={this.onSliderMouseUp}
                            // marks={[{ value: 0, label: '1' }, { value: 200, label: '2' }, { value: 500, label: '3' }]}
                            />

                        </Grid>

                        <Grid item xs={2} align="left">
                            <Typography color="textSecondary">
                                {this.props.scaleLabels.max}
                            </Typography>
                        </Grid>



                    </Grid>


                </div>









            </div>
        );
    }
}
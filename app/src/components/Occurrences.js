import React, { Component } from 'react';
import { Typography } from '@material-ui/core';


import { timestampToDateString } from '../utils'
import { FixedSizeList } from 'react-window';


export default class Occurrences extends Component {
    constructor(props) {
        super(props);
        this.isManualScroll = false
        this.listRef = React.createRef()
        this.onItemsRendered = this.onItemsRendered.bind(this)
    }

    onItemsRendered(items) {


        const occurrence = this.props.occurrences[items.overscanStartIndex]

        if (!this.props.isAnimated) {
            const time = this.props.timeScale(occurrence[0]);
            this.props.timeUpdate(time);
        }
    }

    componentDidUpdate(prevProps) {

        // Allow user to take over the scroller when animation is stopped
        if (this.props.isAnimated) {



            const ts = this.props.timeScale.invert(this.props.time);
            const scrollToRow = this.props.occurrences.filter(function (occ) {
                return occ[0] <= ts
            }).length;
            this.listRef.current.scrollToItem(scrollToRow);
        }
    }

    render() {


        const {
            Row = ({ index, style }) => (

                <div style={style}>

                    <Typography color="textPrimary">{this.props.occurrences[index][2]}</Typography>
                    <Typography color="textSecondary">{timestampToDateString(this.props.occurrences[index][0])}</Typography>
                    <Typography color="textSecondary"><a rel="noopener noreferrer" target="_blank" href={'https://gbif.org/occurrence/' + this.props.occurrences[index][1]}>View record</a></Typography>

                </div>
            ),
            itemCount = this.props.occurrences.length
        } = this.props;



        return (
            <div>
                <Typography color="textPrimary" component="h2" variant="h6">Occurrences collected</Typography>
                <FixedSizeList
                    ref={this.listRef}
                    height={350}
                    itemCount={itemCount}
                    itemSize={85}
                    width={300}
                    onItemsRendered={this.onItemsRendered}
                >

                    {Row}

                </FixedSizeList>
            </div>



        );
    }
}
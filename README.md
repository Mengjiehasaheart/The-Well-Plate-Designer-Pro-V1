# Well Plate Designer Pro

Once upon a time, scientists spent a fraction of their life designing plate experiments and some would spend even more time color-coding their cells in vintage software like Excel, GraphPad, or even PowerPoint (yes boy, we've seen it all). 

This first edition web based interface was created aiming to facilitate this process and help with planning plate experiments faster. No more copy pasting cells, no more manual color picking, and almost definitely no more forgetting which well had what

## So for Quick Start of the GUI, I am using streamlit to host this
you might have to wake the app up sometimes when it's gone to sleep


If running locally, install the requirements first as following: 
```bash
pip install -r requirements.txt
streamlit run app.py
```
then your browser will open to the Well Plate Designer Pro interface. That's it!

## Features

### There are some common plate formats to choose from
- 24-well
- 48-well
- 96-well
- 384-well
- Custom dimensions

### There a few assignment methods to wells
If unsure, using the basic group assignment and treat each new group as a unique combination of your grouping variables
- **Group Assignment**: Assign treatments, controls, and conditions etc.........
- **Serial Dilution**: concentration calculations with gradient visualization
- **Compound Mixtures**: complex mixtures with multiple components
- **Combinatorial Design**: Generate all combinations of multiple factors
- **Time Course**: temporal experiments with replicates
- **Dose Response**: dose-response curves with log or linear scales
- **Custom Patterns**: Checkerboard, stripes, gradients, etc

### Export Options
- **Excel (Plate Layout)**: Visual cell grid matching your screen creation and for presentation purposes
- **Excel (Long Format)**: One row per well
- **CSV**
- **JSON** for programmatic access

## Usage Tips

1. **Start with Groups**: Define your deepest desired treatments/conditions first in the sidebar
2. **Select Wells**: Click individual wells, use range selection (i.e., A1:D4), or use pattern tools
3. **Assign Quickly**: Use the colored group buttons to assign selected wells instantly
4. **Export When Ready**: Choose your most desired format and download

## Development

Note This is the first development release. New features and improvements will be added. Feel free to report issues or suggest features!

## License

(c) 2024 Mengjie Fan. All rights reserved.

---

*Because life's too short to manually color Excel cells.*
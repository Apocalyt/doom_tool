import imageio
import glob
import numpy
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import copy as cp
import csv

images = []

for image_path in glob.glob("./*.png"):
    images.append(imageio.imread(image_path))

colors = []
for image in images:
    rows = image.shape[0]
    cols = image.shape[1]
    for x in range(0, rows):
        for y in range(0, cols):
            r = numpy.int64(image[x,y,0]) << 16
            g = numpy.int64(image[x,y,1]) << 8
            b = numpy.int64(image[x,y,2])

            rgb = r | g | b
            colors.append(rgb)

# Search colors from pallet

for pallet_path in glob.glob("../doom16x16.png"):
    pallet = imageio.imread(pallet_path)

color_index_dict = {}
index_color_dict = {}

rows = pallet.shape[0]
cols = pallet.shape[1]
for x in range(0, rows):
    for y in range(0, cols):
        r = numpy.int64(pallet[x,y,0]) << 16
        g = numpy.int64(pallet[x,y,1]) << 8
        b = numpy.int64(pallet[x,y,2])

        rgb = r | g | b
        hexa = '#{0:06X}'.format(rgb)

        color_index_dict[hexa] = (x,y)
        index_color_dict[(x, y)] = hexa

# Type conversions for plotting

col_dict = {}

for col in colors:
    hexa = '#{0:06X}'.format(col)
    val = col_dict.get(hexa)
    if val is None:
        col_dict[hexa] = 1
    else:
        col_dict[hexa] += 1

for col in col_dict:
    col_dict[col] *= 100.0/len(colors)

sort = [(k, col_dict[k]) for k in sorted(col_dict, key=col_dict.get, reverse=True)]

keys, counts = zip(*sort)
keys_set = set(keys)

key_labels = []

rows = pallet.shape[0]
cols = pallet.shape[1]

for key in keys:
    key_labels.append("{:X}{:X}".format(color_index_dict[key][0], color_index_dict[key][1]) + ", " + key)

# Export
counts_data = []

for key in keys:
    counts_data.append([
        "{:X}{:X}".format(color_index_dict[key][0], color_index_dict[key][1]),
        key,
        col_dict[key]])

for index in index_color_dict:
    if index_color_dict[index] not in keys:
        hex_index = "{:X}{:X}".format(index[0], index[1])
        counts_data.append([hex_index, index_color_dict[index], 0.0])

with open('data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for line in counts_data:
        writer.writerow(line)

# Plotting

fig,ax = plt.subplots(2)

palletplot = ax[0].imshow(pallet)

def to_hex(x, pos):
    return '%X' % int(x)

fmt = ticker.FuncFormatter(to_hex)

ax[0].get_xaxis().set_major_locator(ticker.MultipleLocator(1))
ax[0].get_yaxis().set_major_locator(ticker.MultipleLocator(1))
ax[0].get_xaxis().set_major_formatter(fmt)
ax[0].get_yaxis().set_major_formatter(fmt)

bar = ax[1].bar(range(len(counts)), counts, align='center', color=keys)
plt.sca(ax[1])

plt.xticks(range(len(key_labels)), key_labels, rotation='vertical')

fig.tight_layout()

plt.show()

selected_hexa = set()
selected_indices = set()
current_keys = cp.copy(keys)

def update_selection(selection_set, value):
    if value in selection_set:
        selection_set.discard(value)
    else:
        selection_set.add(value)

def updated_pallet(highlighted, selected_indices):
    temp_pallet = cp.copy(pallet)

    for key in selected_indices:
        temp_pallet[key[0], key[1], 0] = 0
        temp_pallet[key[0], key[1], 1] = 255
        temp_pallet[key[0], key[1], 2] = 255

    if highlighted is not None:
        r = temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 0]
        g = temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 1]
        b = temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 2]
        if (numpy.int64(r) + numpy.int64(g) + numpy.int64(b)) > 382:
            temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 0] = 0
            temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 1] = 0
            temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 2] = 0
        else:
            temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 0] = 255
            temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 1] = 255
            temp_pallet[color_index_dict[highlighted][0], color_index_dict[highlighted][1], 2] = 255

    return temp_pallet

def hover(event):
    if event.inaxes == ax[1]:
        if round(event.xdata) >= 0 and round(event.xdata) < len(keys):
            key = current_keys[int(round(event.xdata))]

            temp_pallet = updated_pallet(key, selected_indices)
            ax[0].imshow(temp_pallet)
            fig.canvas.draw()

def click(event):
    if event.inaxes == ax[0]:
        if round(event.xdata) >= 0 and round(event.xdata) < pallet.shape[0]:
            if round(event.ydata) >= 0 and round(event.ydata) < pallet.shape[1]:

                index = (int(round(event.ydata)), int(round(event.xdata)))
                update_selection(selected_indices, index)

                hexa = index_color_dict[(index[0], index[1])]

                update_selection(selected_hexa, hexa)

                temp_col_dict = {}
                if selected_hexa:
                    for hexa in selected_hexa:
                        if hexa in col_dict:
                            temp_col_dict[hexa] = col_dict[hexa]
                if not temp_col_dict:
                    temp_col_dict = col_dict.copy()

                sort = [(k, temp_col_dict[k]) for k in sorted(temp_col_dict, key=temp_col_dict.get, reverse=True)]
                temp_keys, temp_counts = zip(*sort)
                global current_keys
                current_keys = cp.copy(temp_keys)
                ax[1].clear()
                ax[1].bar(range(len(temp_counts)), temp_counts, align='center', color=temp_keys)

                key_labels = []
                for key in temp_keys:
                    key_labels.append("{:X}{:X}".format(color_index_dict[key][0], color_index_dict[key][1]) + ", " + key)
                plt.xticks(range(len(key_labels)), key_labels, rotation='vertical')

                temp_pallet = updated_pallet(None, selected_indices)
                ax[0].imshow(temp_pallet)
                fig.canvas.draw()

fig.canvas.mpl_connect("motion_notify_event", hover)
fig.canvas.mpl_connect("button_press_event", click)

#!/usr/bin/python

import os
import math
import platform

import cv2
import numpy as np
import skimage.transform as st

ROOT = '../matlab/'

def im2double(img):
    result = np.zeros(img.shape, np.float64)
    height, width = result.shape
    for i in range(height):
        for j in range(width):
            result[i, j] = img[i, j] / 255.

    return result

def get_mean(img, T):
    sum_larger = 0
    sum_smaller = 0
    count_larger = 0
    count_smaller = 0
    for column in img:
        for intansity in column:
            if intansity >= T:
                sum_larger += intansity
                count_larger += 1
            else:
                sum_smaller += intansity
                count_smaller += 1

    return 0.5 * ((sum_larger + 0.0) / count_larger + (sum_smaller + 0.0) / count_smaller)

def myprewittedge(Im, T, direction):
    height, width = Im.shape
    g = np.zeros(Im.shape, np.uint8)

    # Algorithm 1: Automatically determined threshold
    if T == None:
        T = 0.5 * (np.max(Im) + np.min(Im))
        previous = T
        for i in range(10):
            T = get_mean(Im, T)
            if 0.05 * previous > abs(T - previous):
                break
            previous = T

    filter0 = None
    filter1 = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
    filter2 = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    filter3 = np.array([[-1, -1, 0], [-1, 0, 1], [0, 1, 1]])
    filter4 = np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]])

    if direction == 'all':
        for i in range(1, height - 1):
            for j in range(1, width - 1):
                curr_sub_region = np.array([[Im[i - 1, j - 1], Im[i - 1, j], Im[i - 1, j + 1]],
                                            [Im[i, j - 1],     Im[i, j],     Im[i, j + 1]],
                                            [Im[i + 1, j - 1], Im[i + 1, j], Im[i + 1, j + 1]]])
                temp = np.sum(filter1 * curr_sub_region)
                if abs(temp) >= T:
                    g[i, j] = 255
                    continue

                temp = np.sum(filter2 * curr_sub_region)
                if abs(temp) >= T:
                    g[i, j] = 255
                    continue
            
                temp = np.sum(filter3 * curr_sub_region)
                if abs(temp) >= T:
                    g[i, j] = 255
                    continue

                temp = np.sum(filter4 * curr_sub_region)
                if abs(temp) >= T:
                    g[i, j] = 255
    else:
        if direction == 'horizontal':
            filter0 = filter1
        elif direction == 'vertical':
            filter0 = filter2
        elif direction == 'pos45':
            filter0 = filter3
        elif direction == 'neg45':
            filter0 = filter4

        for i in range(1, height - 1):
            for j in range(1, width - 1):
                curr_sub_region = np.array([[Im[i - 1, j - 1], Im[i - 1, j], Im[i - 1, j + 1]],
                                            [Im[i, j - 1],     Im[i, j],     Im[i, j + 1]],
                                            [Im[i + 1, j - 1], Im[i + 1, j], Im[i + 1, j + 1]]])
                temp = np.sum(filter0 * curr_sub_region)
                if abs(temp) >= T:
                    g[i, j] = 255

    return g

def Task1():
    Im = cv2.imread(ROOT + 'fig.tif', cv2.IMREAD_UNCHANGED)
    # cv2.imshow('./01original.jpg', Im)
    cv2.imwrite('./01original.jpg', Im)
    # cv2.waitKey(2000)
    return Im

def Task2(Im):
    threshold = np.max(Im) * 0.2
    g = myprewittedge(Im, threshold, "all")
    # cv2.imshow('./02binary1.jpg', g)
    cv2.imwrite('./02binary1.jpg', g)
    # cv2.waitKey(2000)
    return g

def Task3(Im):
    f = myprewittedge(Im, None, "all")
    # cv2.imshow('./03binary2.jpg', f)
    cv2.imwrite('./03binary2.jpg', f)
    # cv2.waitKey(2000)
    return f

def get_top_peaks(peaks, num):
    result = []
    for i in range(min(num, len(peaks[0]))):
        result.append((peaks[0][i], peaks[1][i], peaks[2][i]))

    return result

def get_correspond_int(f):
    if f - int(f) >= 0.5:
        return int(f) + 1
    else:
        return int(f)

def find_lines(BW, peaks):
    [row, col] = BW.shape
    lines = []

    for intancity, angle, dist in peaks:
        min_x = 0
        min_y = 0

        x0 = dist / np.cos(angle)
        b = dist / np.sin(angle)
        k = -1 * (b / x0)
        max_x = min(col - 1, get_correspond_int(x0))
        max_y = min(row - 1, get_correspond_int(b))
        min_x = get_correspond_int((max_y - b) / k)
        min_y = get_correspond_int(k * max_x + b)

        if (max_y - min_y) > (max_x - min_x):
            start_point = (min_y, max_x)
            end_point = (min_y, max_x)
            start = False
            skip = 0
            for i in range(min_y, max_y + 1):
                xi = get_correspond_int((i - b) / k)
                edge = False
                for j in range(-2, 3):
                    if BW[i, xi + j] == 255:
                        edge = True
                        break
                if edge:
                    skip = 0
                    if not start:
                        start = True
                        start_point = (i, xi)
                else:
                    skip += 1
                    if start:
                        if skip > 10:
                            start = False
                            end_point = (i - 1, get_correspond_int((i - 1 - b) / k))
                            lines.append((start_point, end_point))
        else:
            start_point = (min_y, max_x)
            end_point = (min_y, max_x)
            start = False
            skip = 0
            for i in range(min_x, max_x + 1):
                yi = get_correspond_int(k * i + b)
                edge = False
                for j in range(-2, 3):
                    if BW[yi + j, i] == 255:
                        edge = True
                        break
                if edge:
                    skip = 0
                    if not start:
                        start_point = (yi, i)
                else:
                    skip += 1
                    if start:
                        if skip > 10:
                            start = False
                            end_point = get_correspond_int((k * (i - 1) + b), i - 1)
                            lines.append((start_point, end_point))

    return lines

def Task4(BW):
    H, theta, d = st.hough_line(BW)
    peaks = st.hough_line_peaks(H, theta, d)
    peaks = get_top_peaks(peaks, 5)
    print(peaks)
    lines = find_lines(BW, peaks)

    Im = cv2.imread(ROOT + 'fig.tif')

    max_sp = ()
    max_ep = ()
    max_length = 0
    for sp, ep in lines:
        length = ((sp[0] - ep[0]) ** 2) * ((sp[1] - ep[1]) ** 2)
        print(sp, ep, length)
        if length > max_length:
            max_sp = sp
            max_ep = ep
            max_length = length

    print(max_sp, max_ep)
    cv2.circle(Im, (max_sp[1], max_sp[0]), 4, (0, 0, 255), 2)
    cv2.circle(Im, (max_ep[1], max_ep[0]), 4, (0, 0, 255), 2)
    cv2.line(Im, (max_sp[1], max_sp[0]), (max_ep[1], max_ep[0]), (255, 0, 0), 2)
    cv2.imwrite('./04longestline.jpg', Im)
    # cv2.imshow('houghline', Im)
    # cv2.waitKey(10000)

def sift(image):

    cv2.imwrite('tmp.pgm', image)

    command = ''
    sysstr = platform.system()
    if sysstr == 'Windows':
        command = 'siftWin32'
    else:
        command = './sift'
    command += ' < tmp.pgm > tmp.key'
    os.system(command)

    g = open('tmp.key', 'r')
    header = g.readline().strip().split()
    if len(header) != 2:
        print('Error: Invalid keypoint file beginning.')
        return

    num = int(header[0])
    length = int(header[1])
    if length != 128:
        print('Error: Keypoint descriptor length invalid (should be 128).')

    locs = np.zeros((num, 4))
    descriptors = np.zeros((num, 128))
    for i in range(num):
        loc = g.readline().strip().split()
        for j in range(4):
            locs[i, j] = float(loc[j])

        des = []
        for j in range(7):
            des += g.readline().strip().split()
        for j in range(128):
            descriptors[i, j] = float(des[j])

    g.close()
    return descriptors, locs

def normalize(des):
    ret = np.zeros(des.shape)
    num, length = des.shape
    for i in range(num):
        len_sq = 0.0
        for j in range(length):
            len_sq += des[i, j] ** 2

        len_inv = 1.0 / math.sqrt(len_sq)
        for j in range(length):
            ret[i, j] = des[i, j] * len_inv

    return ret

def match(des1, des2):
    des1 = normalize(des1)
    des2 = normalize(des2)
    matches = []
    distRatio = 0.6
    des2t = des2.T
    num, length = des1.shape
    for i in range(num):
        dotprods = np.dot(des1[i, :].reshape(1, 128), des2t)
        dotprods = np.arccos(dotprods)
        mapper = {}
        for j in range(dotprods.shape[1]):
            mapper[j] = dotprods[0, j]
        mapper = sorted(mapper.items(), key = lambda x: x[1])
        if (mapper[0][1] < distRatio * mapper[1][1]):
            matches.append((i, mapper[0][0]))

    return matches

def screenmatches(I1, I2, matches, loc1match, des1match, loc2match, des2match):
    initial_len = len(matches[0])
    allScales = np.zeros((1, initial_len))
    allAngs = np.zeros((1, initial_len))
    allX = np.zeros((1, initial_len))
    allY = np.zeros((1, initial_len))
    for i in range(initial_len):
        print('Match %d: image 1 (scale, orient = %f, %f) matches, image2 (scale, orient = %f, %f)'
              % (i + 1, loc1match[i, 2], loc1match[i, 3], loc2match[i, 2], loc2match[i, 3]))
        scaleRatio = loc1match[i, 2] / loc2match[i, 2]
        dTheta = loc1match[i, 3] - loc2match[i, 3]

        # Force dTheta to be between -pi and +pi
        while dTheta > np.pi:
            dTheta -= 2 * np.pi
        while dTheta < -np.pi:
            dTheta += 2 * np.pi

        allScales[0, i] = scaleRatio
        allAngs[0, i] = dTheta

        # the feature in image 1
        x1 = loc1match[i, 0]
        y1 = loc1match[i, 1]

        # the feature in image 2
        x2 = loc2match[i, 0]
        y2 = loc2match[i, 1]

        '''
            The "center" of the object in image 1 is located at an offset of
            (-x1, -y1) relative to the detected feature. We need to scale and rotate
            this offset and apply it to the image2 location
        '''
        offset = np.array([-x1, -y1]).T
        offset = offset / scaleRatio
        # coefficients = np.array([[np.cos(dTheta), abs(np.sin(dTheta))], [-abs(np.sin(dTheta)), np.cos(dTheta)]])
        coefficients = np.array([[np.cos(dTheta), np.sin(dTheta)], [-np.sin(dTheta), np.cos(dTheta)]])
        offset = np.dot(coefficients, offset)

        allX[0, i] = x2 + offset[0]
        allY[0, i] = y2 + offset[1]

    '''
        Use a corase Hough space.
        Dimensions are [angle, scale, x, y]
        Define bin centers
    '''
    aBin = []
    i = -np.pi
    while i <= np.pi:
        aBin.append(i)
        i += np.pi / 4
    aBin = np.array(aBin)

    sBin = []
    i = 0.5
    while i <= 10:
        sBin.append(i)
        i += 2
    sBin = np.array(sBin)

    row, col = I2.shape
    xBin = []
    i = 0
    while i <= col - 1:
        xBin.append(i)
        i += col / 5
    xBin = np.array(xBin)

    yBin = []
    i = 0
    while i <= row - 1:
        yBin.append(i)
        i += row / 5
    yBin = np.array(yBin)

    H = np.zeros((len(aBin), len(sBin), len(xBin), len(yBin)))

    for i in range(initial_len):
        a = allAngs[0, i]
        s = allScales[0, i]
        x = allX[0, i]
        y = allY[0, i]

        # Find bin that is closet to a, s, x, y
        temp = abs(a - aBin)
        ia = 0
        for i in range(len(temp)):
            if temp[i] < temp[ia]:
                ia = i

        temp = abs(s - sBin)
        iS = 0
        for i in range(len(temp)):
            if temp[i] < temp[iS]:
                iS = i

        temp = abs(x - xBin)
        ix = 0
        for i in range(len(temp)):
            if temp[i] < temp[ix]:
                ix = i

        temp = abs(y - yBin)
        iy = 0
        for i in range(len(temp)):
            if temp[i] < temp[iy]:
                iy = i

        H[ia, iS, ix, iy] += 1

    # Find all bins with 3 or more features
    Bin_index = []
    l1, l2, l3, l4 = H.shape
    for i in range(l1):
        for j in range(l2):
            for k in range(l3):
                for l in range(l4):
                    if H[i, j, k, l] >= 3:
                        Bin_index.append((i, j, k, l))

    print('Peaks in the Hough array:')
    for i in range(len(Bin_index)):
        print('%d: %d points, (a, s, x, y) = %f, %f, %f, %f'
              % (i + 1, H[Bin_index[i][0], Bin_index[i][1], Bin_index[i][2], Bin_index[i][3]],
                 aBin[Bin_index[i][0]], sBin[Bin_index[i][1]],
                 xBin[Bin_index[i][2]], yBin[Bin_index[i][3]]))

    # Get the features corresponding to the largest bin
    nFeatures = np.max(H)
    print('Largest bin contains %d features' % nFeatures)
    Bin_index = []
    for i in range(l1):
        for j in range(l2):
            for k in range(l3):
                for l in range(l4):
                    if H[i, j, k, l] == nFeatures:
                        Bin_index.append((i, j, k, l))

    indices = []
    for idx in range(initial_len):
        a = allAngs[0, idx]
        s = allScales[0, idx]
        x = allX[0, idx]
        y = allY[0, idx]

        # Find bin that is closest to a, s, x, y
        temp = abs(a - aBin)
        ia = 0
        for i in range(len(temp)):
            if temp[i] < temp[ia]:
                ia = i

        temp = abs(s - sBin)
        iS = 0
        for i in range(len(temp)):
            if temp[i] < temp[iS]:
                iS = i

        temp = abs(x - xBin)
        ix = 0
        for i in range(len(temp)):
            if temp[i] < temp[ix]:
                ix = i

        temp = abs(y - yBin)
        iy = 0
        for i in range(len(temp)):
            if temp[i] < temp[iy]:
                iy = i

        if ia == Bin_index[0][0] and iS == Bin_index[0][1] and ix == Bin_index[0][2] and iy == Bin_index[0][3]:
            indices.append(idx)

    print('Features belonging to highest peak:')
    print(indices)
    return indices

def drawMatches(I1, I2, loc1, loc2, indices, path):
    h1, w1 = I1.shape
    h2, w2 = I2.shape

    I1 = cv2.imread(ROOT + 'QR-Code.png')
    I2 = cv2.imread(ROOT + 'image1.png')

    matches_img = np.zeros((h1, w1 + w2, 3), np.uint8)
    matches_img[: h1, : w1] = I1
    matches_img[: h2, w1 : w1 + w2] = I2

    for idx in indices:
        (x1, y1) = (int(loc1[idx][1]), int(loc1[idx][0]))
        (x2, y2) = (int(loc2[idx][1]) + w1, int(loc2[idx][0]))
        cv2.line(matches_img, (x1, y1), (x2, y2), (255, 0, 0))
        cv2.putText(matches_img, str(idx + 1), (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255))
        cv2.putText(matches_img, str(idx + 1), (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255))

    cv2.imwrite(path, matches_img)
    # cv2.imshow('path', matches_img)
    # cv2.waitKey(10000)

def mysiftalignment(I1, feature1, I2, feature2, out_path):
    des1, loc1 = feature1
    des2, loc2 = feature2

    matches = match(des1, des2)
    print('%d matches points.' % len(matches))

    matches = np.array(matches).T
    des1_match = des1[matches[0, :], :]
    loc1_match = loc1[matches[0, :], :]
    des2_match = des2[matches[1, :], :]
    loc2_match = loc2[matches[1, :], :]

    indices = screenmatches(I1, I2, matches, loc1_match, des1_match, loc2_match, des2_match)
    print('%d indices point.' % len(indices))
    indices = np.array(indices)
    matches = matches[:, indices]
    drawMatches(I1, I2, loc1_match, loc2_match, indices, out_path)
    return len(indices)

def findBestMatching(I, I1, I2, I3):
    num = np.zeros((1, 3))
    output1 = '05QR_img1.png'
    output2 = '06QR_img2.png'
    output3 = '07QR_img3.png'

    des0, loc0 = sift(I)
    des1, loc1 = sift(I1)
    # des2, loc2 = sift(I2)
    # des3, loc3 = sift(I3)

    num[0, 0] = mysiftalignment(I, [des0, loc0], I1, [des1, loc1], output1)
    # num[0, 1] = mysiftalignment(I, [des0, loc0], I2, [des2, loc2], output2)
    # num[0, 2] = mysiftalignment(I, [des0, loc0], I3, [des3, loc3], output3)

    index = 0
    for i in range(3):
        if num[0, i] > num[0, index]:
            index = i

    return index + 1

def Task5():
    I = cv2.imread(ROOT + 'QR-Code.png', cv2.IMREAD_UNCHANGED)
    I1 = cv2.imread(ROOT + 'image1.png', cv2.IMREAD_UNCHANGED)
    I2 = cv2.imread(ROOT + 'image2.png', cv2.IMREAD_UNCHANGED)
    I3 = cv2.imread(ROOT + 'image3.png', cv2.IMREAD_UNCHANGED)

    n = findBestMatching(I, I1, I2, I3)
    print('The image matches QR-code.jpg best is image %d.jpg' % n)

def main():
    # Im = Task1()
    # print('Original image is read and displayed successfully.')
    # Im = im2double(Im)
    # g = Task2(Im)
    # print('The corresponding binary edge image is computed and dispalyed successfully.')
    # f = Task3(Im)
    # print('The corresponding binary edge image is computed and displayed successfully.')
    # f = cv2.imread('./03binary2.jpg', cv2.IMREAD_UNCHANGED)
    # Task4(f)
    Task5()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
import numpy as np
from astropy.stats import sigma_clipped_stats

# TODO: once astropy photometry is released and stable everything in this file should most likely be removed and replaced with calls to the astropy phot package. 
#  (but needed something quick-and-dirty)

class Error(Exception):
    pass

def centroid(im, x0, y0, searchboxsize=5, centroidboxsize=9):
    """
    im - 2-d numpy array
    x0, y0 - initial x,y
    searchboxsize - search for peak value within this box
    centroidboxsize - calculate centroid of this size box around maximum
    
    returns x,y
    ---
    Note: minimal error-checking as intend to replace this some day with astropy photometry package once it is stable and released
    """
    xmax0 = int(np.round(x0 - searchboxsize/2))
    ymax0 = int(np.round(y0 - searchboxsize/2))
    # in case of multiple maxima, want mean position
    subim = im[xmax0:xmax0 + searchboxsize, ymax0:ymax0 + searchboxsize]
    xmax, ymax = [b.mean() for b in np.where(subim == subim.max())]
    xmax = int(np.round(xmax + xmax0 - centroidboxsize/2))
    ymax = int(np.round(ymax + ymax0 - centroidboxsize/2))
    subim = im[xmax:xmax + centroidboxsize, ymax:ymax + centroidboxsize]
    subim_x = np.outer(np.ones(subim.shape[0]), np.arange(subim.shape[1]) + xmax)
    subim_y = np.outer(np.arange(subim.shape[0]) + ymax, np.ones(subim.shape[1]))
    return (subim_x*subim).sum()/subim.sum(), (subim_y*subim).sum()/subim.sum()


def aperture_phot(im, x, y, star_radius, sky_inner_radius, sky_outer_radius, 
                  return_distances=False):
    """
    im - 2-d numpy array
    x,y - coordinates of center of star
    star_radius - radius of photometry circle
    sky_inner_radius, sky_outer_radius - defines annulus for determining sky
    ----
    Note that this is a very quick-and-dirty aperture photometry routine.
    No error checking.
    No partial pixels.
    Many ways this could fail and/or give misleading results.
    Not to be used within 12 hours of eating food.
    Use only immediately after a large meal.
    ----
    returns dictionary with:
    flux - sky-subtracted flux inside star_radius
    sky_per_pixel - sky counts per pixel determined from sky annulus
    sky_per_pixel_err - estimated 1-sigma uncertainty in sky_per_pixel
    sky_err - estimated 1-sigma uncertainty in sky subtraction from flux
    n_star_pix - number of pixels in star_radius
    n_sky_pix - number of pixels in sky annulus
    x - input x
    y - input y
    star_radius - input star_radius
    sky_inner_radius - input sky_inner_radius
    sky_outer_radius - input sky_outer_radius 
    """
    output = {'x': x, 'y': y, 'star_radius': star_radius,
              'sky_inner_radius': sky_inner_radius, 'sky_outer_radius': sky_outer_radius}
    xdist = np.outer(np.ones(im.shape[0]), np.arange(im.shape[1]) - x)
    ydist = np.outer(np.arange(im.shape[0]) - y, np.ones(im.shape[1]))
    dist = np.sqrt(xdist**2 + ydist**2)
    star_mask = dist <= star_radius
    star_pixels = im[star_mask]
    sky_pixels = im[(dist >= sky_inner_radius) & (dist <= sky_outer_radius)]
    output['n_star_pix'] = star_pixels.size
    output['n_sky_pix'] = sky_pixels.size
    sky_per_pixel, median, stddev = sigma_clipped_stats(sky_pixels)
    sky_per_pixel_err = stddev/np.sqrt(sky_pixels.size)
    output['sky_per_pixel'] = sky_per_pixel
    # TODO: check that are doing sky_per_pixel_err right.  In one quick test seemed high (but maybe wasn't a good test)
    output['sky_per_pixel_err'] = sky_per_pixel_err
    output['flux'] = star_pixels.sum() - sky_per_pixel*star_pixels.size
    output['sky_err'] = sky_per_pixel_err*np.sqrt(star_pixels.size)
    if return_distances:
        output['distances'] = dist
    return output
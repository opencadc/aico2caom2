# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2023.                            (c) 2023.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************

"""
DB - 06-05-20
Thumbnails and Previews are proprietary for science datasets.

"""

import matplotlib.pyplot as plt
import numpy as np

from astropy.io import fits
from astropy.visualization import ZScaleInterval, SqrtStretch, ImageNormalize

from caom2 import ReleaseType, ProductType
from caom2pipe import manage_composable as mc


class AICOPreview(mc.PreviewVisitor):
    def __init__(self, mime_type, **kwargs):
        super().__init__(ReleaseType.DATA, mime_type, **kwargs)
        self._ext = 0

    def generate_plots(self, obs_id):
        count = 0
        self._logger.info(f'Building preview and thumbnail with {self._science_fqn} for {obs_id}')
        self._hdu_list = fits.open(self._science_fqn)

        count += self._do_skycam()

        if count == 2:
            self.add_preview(self._storage_name.thumb_uri, self._storage_name.thumb, ProductType.THUMBNAIL)
            self.add_preview(self._storage_name.prev_uri, self._storage_name.prev, ProductType.PREVIEW)
            self.add_to_delete(self._thumb_fqn)
            self.add_to_delete(self._preview_fqn)
        return count

    def _do_skycam(self):
        image_data = self._hdu_list[self._ext].data
        norm = ImageNormalize(image_data, interval=ZScaleInterval(), stretch=SqrtStretch())
        plt.imshow(image_data, cmap='gray', norm=norm)
        plt.gca().invert_yaxis()
        plt.axis('off')
        with np.errstate(invalid='ignore'):
            plt.savefig(self._preview_fqn, dpi=200, bbox_inches='tight', pad_inches=0, format='png')
        count = 1
        count += self._gen_thumbnail()
        return count


def visit(observation, **kwargs):
    previewer = AICOPreview(mime_type='image/png', **kwargs)
    return previewer.visit(observation)

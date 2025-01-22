# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2025.                            (c) 2025.
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
#

"""
This module implements the ObsBlueprint mapping, as well as the workflow entry point that executes the workflow.
"""

from os.path import basename

from caom2 import DataProductType, ObservationIntentType, ProductType
from caom2pipe import astro_composable as ac
from caom2pipe import caom_composable as cc
from caom2pipe import manage_composable as mc


__all__ = ['AICOMapping', 'AICOName', 'SkyCam']


class AICOName(mc.StorageName):
    """Naming rules:
    - support mixed-case file name storage, and mixed-case obs id values
    - support uncompressed files in storage
    """

    AICO_NAME_PATTERN = '*'

    def __init__(self, source_names):
        super().__init__(source_names=source_names)

    def is_derived(self):
        return False

    def is_skycam_image(self):
        # TODO this needs to be corrected
        return self._file_name.startswith('a')

    def is_valid(self):
        return True


class AICOMapping(cc.TelescopeMapping2):

    def accumulate_blueprint(self, bp):
        """Configure the telescope-specific ObsBlueprint at the CAOM model
        Observation level."""
        self._logger.debug('Begin accumulate_bp.')
        super().accumulate_blueprint(bp)
        self._logger.debug('Done accumulate_bp.')

    def update(self, file_info):
        """Called to fill multiple CAOM model elements and/or attributes
        (an n:n relationship between TDM attributes and CAOM attributes).
        """
        super().update(file_info)
        return self._observation

    def _update_artifact(self, artifact):
        pass


class SkyCam(cc.TelescopeMapping2):

    def configure_axes(self, bp):
        bp.configure_time_axis(1)

    def accumulate_blueprint(self, bp):
        super().accumulate_blueprint(bp)
        self.configure_axes(bp)
        # bp.set('Observation.metaRelease', 'get_release_date()')
        bp.set('Observation.intent', ObservationIntentType.CALIBRATION)
        bp.clear('Observation.algorithm.name')
        bp.set('Observation.telescope.geoLocationX', 'get_geo_x()')
        bp.set('Observation.telescope.geoLocationY', 'get_geo_y()')
        bp.set('Observation.telescope.geoLocationZ', 'get_geo_z()')

        bp.set('Plane.calibrationLevel', 1)
        bp.set('Plane.dataProductType', DataProductType.IMAGE)
        bp.add_attribute('Plane.dataRelease', 'RELEASE')
        bp.add_attribute('Plane.metaRelease', 'RELEASE')
        bp.set('Plane.provenance.project', 'AICO Science Archive')
        bp.set('Plane.provenance.name', 'AICO Sky Camera image')
        bp.set('Plane.provenance.reference', 'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/aico/')
        bp.add_attribute('Plane.provenance.version', 'SWCREATE')

        bp.set('Artifact.productType', ProductType.CALIBRATION)
        bp.set('Artifact.releaseType', 'data')

        bp.set('Chunk.time.axis.axis.ctype', 'TIME')
        bp.set('Chunk.time.axis.axis.cunit', 'd')
        bp.set('Chunk.time.axis.function.naxis', '1')
        bp.set('Chunk.time.axis.function.delta', 'get_time_axis_delta()')
        bp.set('Chunk.time.axis.function.refCoord.pix', '0.5')
        bp.set('Chunk.time.axis.function.refCoord.val', 'get_time_axis_val()')
        bp.add_attribute('Chunk.time.exposure', 'EXPOSURE')
        bp.add_attribute('Chunk.time.resolution', 'EXPOSURE')

        # derived observations
        if AICOName.is_derived(self._storage_name.file_uri):
            bp.set('DerivedObservation.members', [])
            bp.add_attribute('Observation.algorithm.name', 'PROCNAME')

    def get_geo_x(self, ext):
        x, ign1, ign2 = self._get_geo(ext)
        return x

    def get_geo_y(self, ext):
        x, y, ign2 = self._get_geo(ext)
        return y

    def get_geo_z(self, ext):
        x, ign1, z = self._get_geo(ext)
        return z

    def get_time_axis_delta(self, ext):
        exptime = self.get_time_exposure(ext)
        return exptime / (24.0 * 3600.0)

    def get_time_axis_val(self, ext):
        date_obs = self._headers[ext].get('DATE-OBS')
        result = ac.get_datetime_mjd(date_obs)
        if result is not None:
            result = result.value
        return result

    def get_time_exposure(self, ext):
        exptime = mc.to_float(self._headers[ext].get('EXPOSURE'))
        if exptime is not None:
            exptime = mc.convert_to_days(exptime)
        return exptime

    def _update_artifact(self, artifact):
        for part in artifact.parts.values():
            for chunk in part.chunks:
                chunk.naxis = None
                chunk.time_axis = None

    def _get_geo(self, ext):
        def _x(value):
            # e.g. long -79:30:22:99 lat +43:46:20:99
            bits = value.split(':')
            degrees = float(bits[0])
            min = float(bits[1]) / 60.0
            sec = float(bits[2]) / 3600.0
            return degrees + min + sec

        site_lat = self._headers[ext].get('SITELAT')
        site_long = self._headers[ext].get('SITELONG')
        if site_lat is not None and site_long is not None:
            return ac.get_location(_x(site_lat), _x(site_long), 100.0)

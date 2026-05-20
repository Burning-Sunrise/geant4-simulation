#include "TPCHit.hh"

void TPCHit::Print()
{
    G4cout << " trackID: " << fTrackID << " \n Energy Deposition "
           << std::setw(7) << G4BestUnit(feDep, "Energy") << "\n Position "
           << std::setw(7) << G4BestUnit(fPos, "Length") << " \n ";
}
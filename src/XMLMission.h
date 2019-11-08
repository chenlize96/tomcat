#pragma once

#include "Mission.h"
#include <string>

namespace tomcat {

  /**
   * The XMLMission class represents the a mission generated by a predefined XML
   * file
   */
  class XMLMission : public Mission {
  public:
    /**
     * Constructor
     */
    XMLMission(const std::string& missionIdOrPathToXML);

    /**
     * Destructor
     */
    ~XMLMission();

  protected:
    /**
     * Builds the world for the Save and Rescue mission
     */
    void buildWorld();

    /**
     * Retrieves the content of an XML which defines the skeleton of the world
     * for the Search and Rescue mission
     * @return
     */
    std::string getWorldSkeletonFromXML();
  };

} // namespace tomcat
